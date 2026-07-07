const state = {
  recipes: [],
  families: [],
  roadmap: [],
  rev2Issues: [],
  rev2Candidates: [],
  query: "",
  ingredient: "",
  familyId: "all",
  status: "all",
  sort: "year-asc",
};

const elements = {
  searchInput: document.querySelector("#searchInput"),
  ingredientInput: document.querySelector("#ingredientInput"),
  familyFilter: document.querySelector("#familyFilter"),
  statusFilter: document.querySelector("#statusFilter"),
  sortSelect: document.querySelector("#sortSelect"),
  clearFilters: document.querySelector("#clearFilters"),
  recipeList: document.querySelector("#recipeList"),
  recipeTemplate: document.querySelector("#recipeTemplate"),
  resultCount: document.querySelector("#resultCount"),
  featuredPie: document.querySelector("#featuredPie"),
  commonFamilyGrid: document.querySelector("#commonFamilyGrid"),
  familyList: document.querySelector("#familyList"),
  sourceList: document.querySelector("#sourceList"),
  timelineChart: document.querySelector("#timelineChart"),
  rev2IssueCount: document.querySelector("#rev2IssueCount"),
  rev2RecipeCandidateCount: document.querySelector("#rev2RecipeCandidateCount"),
  rev2CandidateList: document.querySelector("#rev2CandidateList"),
  scanDialog: document.querySelector("#scanDialog"),
};

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Unable to load ${path}`);
  }
  return response.json();
}

async function loadOptionalJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    return [];
  }
  return response.json();
}

function familyName(familyId) {
  return state.families.find((family) => family.family_id === familyId)?.family_name || familyId;
}

function normalize(value) {
  return String(value || "").toLowerCase();
}

function dayOfYear(date) {
  const start = new Date(date.getFullYear(), 0, 0);
  return Math.floor((date - start) / 86400000);
}

function countsByFamily() {
  const counts = new Map();
  for (const recipe of state.recipes) {
    counts.set(recipe.family_id, (counts.get(recipe.family_id) || 0) + 1);
  }
  return counts;
}

function verificationRank(recipe) {
  if (recipe.verification_status === "rev1_source_text_verified") return 0;
  if (recipe.verification_status === "rev2_source_text_verified") return 1;
  if (recipe.verification_status === "rev3_newspaper_index_verified") return 2;
  if (recipe.verification_status === "rev4_source_manifest_verified") return 3;
  return 4;
}

function sourceTypeLabel(sourceType) {
  const labels = {
    cookbook: "Books",
    magazine: "Magazines",
    newspaper: "Newspapers",
    collection: "Collections / archives",
  };
  if (labels[sourceType]) {
    return labels[sourceType];
  }
  return String(sourceType || "Other sources")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function statusFilterLabel(status) {
  const sourceTypes = Array.from(new Set(
    state.recipes
      .filter((recipe) => recipe.verification_status === status)
      .map((recipe) => recipe.source_type)
      .filter(Boolean)
  ));
  if (sourceTypes.length) {
    return sourceTypes.map(sourceTypeLabel).join(" / ");
  }
  return status.replaceAll("_", " ");
}

function searchableText(recipe) {
  return [
    recipe.title,
    recipe.original_title,
    recipe.source_title,
    recipe.author,
    recipe.publication,
    recipe.original_text,
    recipe.ingredients_original,
    recipe.directions_original,
    recipe.ingredients_modernized,
    recipe.directions_modernized,
    recipe.tags,
    recipe.region,
    recipe.notes,
  ].map(normalize).join(" ");
}

function filteredRecipes() {
  const query = normalize(state.query);
  const ingredient = normalize(state.ingredient);
  return state.recipes
    .filter((recipe) => !query || searchableText(recipe).includes(query))
    .filter((recipe) => state.familyId === "all" || recipe.family_id === state.familyId)
    .filter((recipe) => state.status === "all" || recipe.verification_status === state.status)
    .filter((recipe) => !ingredient || normalize(recipe.ingredients_original).includes(ingredient))
    .sort((a, b) => {
      const rankDifference = verificationRank(a) - verificationRank(b);
      if (rankDifference !== 0) return rankDifference;
      if (state.sort === "year-desc") return b.year - a.year;
      if (state.sort === "title-asc") return a.title.localeCompare(b.title);
      return a.year - b.year;
    });
}

function visibleRecipesForSelectedFamily() {
  if (state.familyId === "all") {
    return [];
  }
  return filteredRecipes();
}

function renderStats() {
  const sources = new Set(state.recipes.map((recipe) => recipe.source_id));
  const structured = state.recipes.filter((recipe) => !recipe.verification_status.includes("pending")).length;
  document.querySelector("#recipeCount").textContent = state.recipes.length;
  document.querySelector("#sourceCount").textContent = sources.size;
  document.querySelector("#familyCount").textContent = state.families.length;
  document.querySelector("#verifiedCount").textContent = structured;
}

function renderFilters() {
  elements.familyFilter.innerHTML = [
    ["all", "Choose a family"],
    ...state.families.map((family) => [family.family_id, family.family_name]),
  ].map(([value, label]) => `<option value="${value}">${label}</option>`).join("");

  const statuses = Array.from(new Set(state.recipes.map((recipe) => recipe.verification_status)))
    .sort((a, b) => verificationRank({ verification_status: a }) - verificationRank({ verification_status: b }));
  elements.statusFilter.innerHTML = [
    ["all", "All source types"],
    ...statuses.map((status) => [status, statusFilterLabel(status)]),
  ].map(([value, label]) => `<option value="${value}">${label}</option>`).join("");
}

function selectFamily(familyId) {
  state.familyId = familyId;
  elements.familyFilter.value = familyId;
  renderRecipes();
  document.querySelector("#recipes").scrollIntoView({ behavior: "smooth" });
}

function makeFamilyButton(family, count) {
  const button = document.createElement("button");
  button.className = "family-card";
  button.type = "button";
  button.dataset.familyId = family.family_id;
  const name = document.createElement("strong");
  const meta = document.createElement("span");
  const action = document.createElement("em");
  name.textContent = family.family_name;
  meta.textContent = `${count.toLocaleString()} recipes | ${family.category}`;
  action.textContent = "View family";
  button.append(name, meta, action);
  button.addEventListener("click", () => selectFamily(family.family_id));
  return button;
}

function renderFeaturedPie(counts) {
  elements.featuredPie.innerHTML = "";
  if (!state.recipes.length) {
    return;
  }
  const featured = state.recipes[dayOfYear(new Date()) % state.recipes.length];
  const panel = document.createElement("article");
  const copy = document.createElement("div");
  const eyebrow = document.createElement("p");
  const title = document.createElement("h3");
  const meta = document.createElement("p");
  const button = document.createElement("button");
  panel.className = "featured-card";
  eyebrow.className = "eyebrow";
  eyebrow.textContent = "Featured pie of the day";
  title.textContent = featured.title;
  meta.textContent = `${familyName(featured.family_id)} | ${featured.year || "year TBD"} | ${featured.source_title}`;
  button.type = "button";
  button.textContent = `View ${familyName(featured.family_id)}`;
  button.addEventListener("click", () => selectFamily(featured.family_id));
  copy.append(eyebrow, title, meta);
  panel.append(copy, button);
  elements.featuredPie.append(panel);
}

function renderCommonFamilyCards() {
  const counts = countsByFamily();
  renderFeaturedPie(counts);
  elements.commonFamilyGrid.innerHTML = "";
  const commonFamilies = state.families
    .filter((family) => counts.has(family.family_id))
    .sort((a, b) => counts.get(b.family_id) - counts.get(a.family_id))
    .slice(0, 12);
  const fragment = document.createDocumentFragment();
  for (const family of commonFamilies) {
    fragment.append(makeFamilyButton(family, counts.get(family.family_id)));
  }
  elements.commonFamilyGrid.append(fragment);
}

function metadataItem(label, value) {
  const wrapper = document.createElement("div");
  const term = document.createElement("dt");
  const description = document.createElement("dd");
  term.textContent = label;
  description.textContent = value || "TBD";
  wrapper.append(term, description);
  return wrapper;
}

function recipeCopyFor(recipe) {
  return recipe.directions_original
    || recipe.original_text
    || recipe.directions_modernized
    || recipe.ingredients_original
    || "Recipe transcription is queued for enrichment.";
}

function ingredientsFor(recipe) {
  return recipe.ingredients_original
    || recipe.ingredients_modernized
    || "";
}

function ingredientItemsFor(recipe) {
  const ingredients = ingredientsFor(recipe);
  if (!ingredients) {
    return [];
  }
  const separator = ingredients.includes(";") ? /;\s*/ : /,\s*/;
  return ingredients
    .split(separator)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function renderIngredients(section, recipe) {
  const list = section.querySelector("ul");
  const fallback = section.querySelector("p");
  const items = ingredientItemsFor(recipe);
  list.innerHTML = "";
  if (!items.length) {
    fallback.hidden = false;
    fallback.textContent = "Ingredients are preserved in the original recipe text below.";
    return;
  }
  fallback.hidden = true;
  fallback.textContent = "";
  for (const item of items) {
    const listItem = document.createElement("li");
    listItem.textContent = item;
    list.append(listItem);
  }
}

function applySourceLink(link, recipe) {
  const url = String(recipe.source_url || "").trim();
  link.textContent = "Original Source";
  link.title = `Open original source for ${recipe.title}`;
  if (url.startsWith("http://") || url.startsWith("https://")) {
    link.href = url;
    link.classList.remove("recipe-card__source--disabled");
    link.removeAttribute("aria-disabled");
    return;
  }
  link.removeAttribute("href");
  link.classList.add("recipe-card__source--disabled");
  link.setAttribute("aria-disabled", "true");
  link.title = "Original source link is not available for this record.";
}

function sourceScanFor(recipe) {
  const url = String(recipe.source_url || "").trim();
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    return null;
  }
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("archive.org")) {
      const parts = parsed.pathname.split("/").filter(Boolean);
      const itemIndex = parts.findIndex((part) => part === "details" || part === "download");
      const identifier = itemIndex >= 0 ? parts[itemIndex + 1] : "";
      if (identifier) {
        return {
          fullUrl: `https://archive.org/services/img/${identifier}`,
          caption: "Archive.org source scan",
          sourceUrl: url,
        };
      }
    }
    if (parsed.hostname.includes("gutenberg.org")) {
      const ebookId = parsed.pathname.match(/ebooks\/(\d+)/)?.[1]
        || parsed.pathname.match(/\/(\d+)(?:\/|$)/)?.[1];
      if (ebookId) {
        return {
          fullUrl: `https://www.gutenberg.org/cache/epub/${ebookId}/pg${ebookId}.cover.medium.jpg`,
          caption: "Project Gutenberg source cover",
          sourceUrl: url,
        };
      }
    }
  } catch {
    return null;
  }
  return null;
}

function renderSourceScan(figure, recipe) {
  const scan = sourceScanFor(recipe);
  if (!scan) {
    figure.hidden = true;
    return;
  }
  const button = figure.querySelector("button");
  figure.querySelector("figcaption").textContent = scan.caption;
  button.dataset.fullUrl = scan.fullUrl;
  button.dataset.sourceUrl = scan.sourceUrl;
  button.dataset.recipeTitle = recipe.title;
  button.dataset.caption = scan.caption;
  figure.hidden = false;
}

function openScanDialog(button) {
  if (!elements.scanDialog) {
    return;
  }
  const title = button.dataset.recipeTitle || "Original source scan";
  const caption = button.dataset.caption || "Original source scan";
  const image = elements.scanDialog.querySelector("img");
  elements.scanDialog.querySelector("h3").textContent = title;
  elements.scanDialog.querySelector("a").href = button.dataset.sourceUrl || "#";
  elements.scanDialog.querySelector("p:last-child").textContent = caption;
  image.src = button.dataset.fullUrl;
  image.alt = `Enlarged source scan for ${title}`;
  if (typeof elements.scanDialog.showModal === "function") {
    elements.scanDialog.showModal();
  } else {
    elements.scanDialog.setAttribute("open", "");
  }
}

function renderRecipes() {
  const recipes = visibleRecipesForSelectedFamily();
  elements.recipeList.innerHTML = "";
  if (state.familyId === "all") {
    elements.featuredPie.hidden = false;
    elements.commonFamilyGrid.hidden = false;
    elements.resultCount.textContent = "Select a family";
    renderCommonFamilyCards();
    return;
  }

  elements.featuredPie.hidden = true;
  elements.commonFamilyGrid.hidden = true;
  elements.resultCount.textContent = `${recipes.length.toLocaleString()} ${recipes.length === 1 ? "recipe" : "recipes"}`;

  if (!recipes.length) {
    elements.recipeList.innerHTML = '<p class="empty">No recipes match the current filters.</p>';
    return;
  }

  for (const recipe of recipes) {
    const node = elements.recipeTemplate.content.cloneNode(true);
    node.querySelector("h3").textContent = recipe.title;
    node.querySelector(".recipe-card__year").textContent = recipe.year;
    const sourceLink = node.querySelector(".recipe-card__source");
    applySourceLink(sourceLink, recipe);
    const metadata = node.querySelector(".metadata");
    metadata.append(
      metadataItem("Family", familyName(recipe.family_id)),
      metadataItem("Source", recipe.source_title),
      metadataItem("Author", recipe.author),
      metadataItem("Status", recipe.verification_status.replaceAll("_", " "))
    );
    renderSourceScan(node.querySelector(".recipe-card__scan"), recipe);
    renderIngredients(node.querySelector(".recipe-card__ingredients"), recipe);
    node.querySelector(".recipe-card__copy p").textContent = recipeCopyFor(recipe);
    node.querySelector(".recipe-card__notes").textContent = recipe.notes;
    elements.recipeList.append(node);
  }
}

function renderTimeline() {
  const counts = new Map();
  for (const recipe of state.recipes) {
    counts.set(recipe.year, (counts.get(recipe.year) || 0) + 1);
  }
  const max = Math.max(...counts.values(), 1);
  elements.timelineChart.innerHTML = Array.from(counts.entries())
    .sort(([a], [b]) => a - b)
    .map(([year, count]) => `
      <div class="timeline-row">
        <strong>${year}</strong>
        <div class="timeline-bar" style="width: ${Math.max(12, (count / max) * 100)}%"></div>
        <span>${count}</span>
      </div>
    `).join("");
}

function renderFamilies() {
  const counts = new Map();
  for (const recipe of state.recipes) {
    counts.set(recipe.family_id, (counts.get(recipe.family_id) || 0) + 1);
  }
  elements.familyList.innerHTML = state.families
    .filter((family) => counts.has(family.family_id))
    .map((family) => `
      <article class="family-item">
        <strong>${family.family_name}</strong>
        <span>${counts.get(family.family_id)} variants | ${family.category}</span>
      </article>
    `).join("");
}

function renderSources() {
  const sources = new Map();
  for (const recipe of state.recipes) {
    if (!sources.has(recipe.source_id)) {
      sources.set(recipe.source_id, {
        title: recipe.source_title,
        author: recipe.author,
        year: recipe.year,
        url: recipe.source_url,
        count: 0,
      });
    }
    sources.get(recipe.source_id).count += 1;
  }
  elements.sourceList.innerHTML = Array.from(sources.values())
    .sort((a, b) => a.year - b.year)
    .map((source) => `
      <article class="source-item">
        <strong><a href="${source.url}" target="_blank" rel="noreferrer">${source.title}</a></strong>
        <span>${source.author || "Unknown author"} | ${source.year} | ${source.count} recipes</span>
      </article>
    `).join("");
}

function renderRev2Queue() {
  elements.rev2IssueCount.textContent = state.rev2Issues.length;
  elements.rev2RecipeCandidateCount.textContent = state.rev2Candidates.length;
  const samples = state.rev2Candidates.slice(0, 6);
  elements.rev2CandidateList.innerHTML = samples.length
    ? samples.map((candidate) => `
      <article class="candidate-item">
        <strong>${candidate.title_guess || "Untitled OCR context"}</strong>
        <span>${candidate.source_group_id} | ${candidate.year || "year TBD"} | ${candidate.status}</span>
      </article>
    `).join("")
    : '<p class="empty">No Rev2 recipe candidates exported yet.</p>';
}

function render() {
  renderRecipes();
  renderTimeline();
  renderFamilies();
  renderSources();
  renderRev2Queue();
}

function bindEvents() {
  document.querySelector(".hero__search").addEventListener("submit", (event) => {
    event.preventDefault();
    state.query = elements.searchInput.value;
    renderRecipes();
    document.querySelector("#recipes").scrollIntoView({ behavior: "smooth" });
  });
  elements.searchInput.addEventListener("input", (event) => {
    state.query = event.target.value;
    renderRecipes();
  });
  elements.ingredientInput.addEventListener("input", (event) => {
    state.ingredient = event.target.value;
    renderRecipes();
  });
  elements.familyFilter.addEventListener("change", (event) => {
    state.familyId = event.target.value;
    renderRecipes();
  });
  elements.statusFilter.addEventListener("change", (event) => {
    state.status = event.target.value;
    renderRecipes();
  });
  elements.sortSelect.addEventListener("change", (event) => {
    state.sort = event.target.value;
    renderRecipes();
  });
  elements.clearFilters.addEventListener("click", () => {
    state.query = "";
    state.ingredient = "";
    state.familyId = "all";
    state.status = "all";
    state.sort = "year-asc";
    elements.searchInput.value = "";
    elements.ingredientInput.value = "";
    elements.familyFilter.value = "all";
    elements.statusFilter.value = "all";
    elements.sortSelect.value = "year-asc";
    renderRecipes();
  });
  elements.recipeList.addEventListener("click", (event) => {
    const button = event.target.closest(".recipe-card__scan-button");
    if (button) {
      openScanDialog(button);
    }
  });
  elements.scanDialog?.querySelector(".scan-dialog__close")?.addEventListener("click", () => {
    elements.scanDialog.close();
  });
  elements.scanDialog?.addEventListener("click", (event) => {
    if (event.target === elements.scanDialog) {
      elements.scanDialog.close();
    }
  });
}

async function init() {
  [state.recipes, state.families, state.roadmap, state.rev2Issues, state.rev2Candidates] = await Promise.all([
    loadJson("./public/data/recipes.json"),
    loadJson("./public/data/recipe_families.json"),
    loadJson("./public/data/roadmap.json"),
    loadOptionalJson("./public/data/rev2_issue_candidates.json"),
    loadOptionalJson("./public/data/rev2_recipe_candidates.json"),
  ]);
  renderStats();
  renderFilters();
  render();
  bindEvents();
}

init().catch((error) => {
  document.body.innerHTML = `<main class="band"><h1>PieAtlas</h1><p>${error.message}</p></main>`;
});

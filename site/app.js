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

  const statuses = Array.from(new Set(state.recipes.map((recipe) => recipe.verification_status))).sort();
  elements.statusFilter.innerHTML = [
    ["all", "All statuses"],
    ...statuses.map((status) => [status, status.replaceAll("_", " ")]),
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
    sourceLink.href = recipe.source_url;
    const metadata = node.querySelector(".metadata");
    metadata.append(
      metadataItem("Family", familyName(recipe.family_id)),
      metadataItem("Source", recipe.source_title),
      metadataItem("Author", recipe.author),
      metadataItem("Status", recipe.verification_status.replaceAll("_", " "))
    );
    node.querySelector(".recipe-card__ingredients").textContent = recipe.ingredients_original
      ? `Ingredients: ${recipe.ingredients_original}`
      : "Ingredients awaiting transcription.";
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

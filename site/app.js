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
      if (state.sort === "year-desc") return b.year - a.year;
      if (state.sort === "title-asc") return a.title.localeCompare(b.title);
      return a.year - b.year;
    });
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
    ["all", "All families"],
    ...state.families.map((family) => [family.family_id, family.family_name]),
  ].map(([value, label]) => `<option value="${value}">${label}</option>`).join("");

  const statuses = Array.from(new Set(state.recipes.map((recipe) => recipe.verification_status))).sort();
  elements.statusFilter.innerHTML = [
    ["all", "All statuses"],
    ...statuses.map((status) => [status, status.replaceAll("_", " ")]),
  ].map(([value, label]) => `<option value="${value}">${label}</option>`).join("");
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

function renderRecipes() {
  const recipes = filteredRecipes();
  elements.recipeList.innerHTML = "";
  elements.resultCount.textContent = `${recipes.length} ${recipes.length === 1 ? "recipe" : "recipes"}`;

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

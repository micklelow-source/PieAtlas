# PieAtlas PROJECT_SPEC

**Version:** 1.0

## Vision

PieAtlas is an open-source historical research project whose goal is to
become the definitive catalog of public-domain pie recipes published
through 1928.

The archive emphasizes: - Historical accuracy - Verifiable citations -
Public-domain sources - Reproducible harvesting - GitHub-first
development

------------------------------------------------------------------------

# Roadmap

## Rev1

**Target:** 500 verified recipes

Sources: - Major public-domain cookbooks through 1928

Deliverables: - recipes.csv / recipes.json - recipe_families.csv -
source manifests - validation scripts - searchable website

------------------------------------------------------------------------

## Rev2

**Target:** 2,000 recipes

Adds: - Public-domain magazines - Household journals - Regional
publications

------------------------------------------------------------------------

## Rev3

**Target:** 5,000 recipes

Adds: - Historic newspapers - Syndicated recipe columns - Regional
newspaper archives

------------------------------------------------------------------------

## Rev4

**Target:** 10,000+ recipes

Adds: - Church/community cookbooks - USDA publications - Agricultural
extension bulletins - Complete public-domain coverage through 1928

------------------------------------------------------------------------

# Repository Layout

``` text
PieAtlas/
  data/
  docs/
  scripts/
  site/
  images/
  .github/
```

# Recipe Schema

Every recipe should contain:

-   recipe_id
-   title
-   family_id
-   year
-   source_title
-   author
-   publication
-   page
-   source_url
-   rights
-   original_title
-   original_text
-   ingredients_original
-   directions_original
-   ingredients_modernized
-   directions_modernized
-   tags
-   region
-   verification_status
-   duplicate_status
-   notes

# Recipe Families

Group recipes without deleting variants.

Examples: - Apple Pie - Pumpkin Pie - Lemon Meringue Pie - Chess Pie -
Shoofly Pie - Vinegar Pie - Berry Pie - Meat Pie

# Source Priorities

1.  Project Gutenberg
2.  Internet Archive
3.  HathiTrust
4.  Chronicling America
5.  State newspaper archives
6.  USDA publications

# Harvest Workflow

1.  Harvest candidates.
2.  Review OCR.
3.  Verify public-domain status.
4.  Normalize metadata.
5.  Assign recipe family.
6.  Validate.
7.  Export CSV/JSON.
8.  Publish.

# Deduplication Rules

-   Preserve every historical recipe.
-   Group by family_id.
-   Never overwrite a historical variant.
-   Record exact reprints separately.

# Website Features

-   Full-text search
-   Ingredient search
-   Timeline
-   Maps
-   Cookbook pages
-   Recipe family pages
-   Scan viewer
-   JSON API

# Coding Standards

-   Python 3.12+
-   Type hints
-   Black formatting
-   CSV + JSON outputs
-   Unit tests for parsers
-   GitHub Actions for validation

# GitHub Milestones

Rev1: - Complete cookbook extraction - 500 recipes

Rev2: - Magazine extraction - 2,000 recipes

Rev3: - Newspaper extraction - 5,000 recipes

Rev4: - Complete archive - 10,000+ recipes

# Long-Term Goals

-   REST API
-   Static website
-   Research exports
-   Timeline visualizations
-   Ingredient trend analytics
-   Regional maps
-   OCR correction workflow
-   Contributor review system

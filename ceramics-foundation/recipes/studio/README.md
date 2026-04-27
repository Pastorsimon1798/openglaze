# Studio Recipes

> **DEPRECATION NOTE (2026-04-27):** The studio-specific recipes listed below were
> originally compiled for a specific studio. The project is now studio-agnostic.
> Some recipe names reference old studio-specific glazes that have been removed.
> For the current glaze database, see `frontend/scripts/data.js`.

Custom and community recipes. Generic/traditional recipes remain valid.

## Documented Recipes

| Name | Origin | Glazy Reference | File |
|------|--------|-----------------|------|
| John's Red | John Britt | Glazy #398657 | `johns-red.yaml` |
| Malcom's Shino | Malcom Davis | Famous shino specialist | `malcolms-shino.yaml` |
| Strontium Crystal | Pete Pinnell | Glazy #33211 | `strontium-crystal.yaml` |
| Tom Coleman Clear | Tom Coleman | Multiple on Glazy | `tom-coleman-clear.yaml` |
| Tenmoku | Traditional | Multiple versions | `tenmoku.yaml` |
| Celadon | Traditional | Multiple versions | `celadon.yaml` |
| Chun Blue | Traditional | Cindy Wennin variation | `chun-blue.yaml` |
| Tea Dust | Traditional | Multiple versions | See notes |
| Iron Red | Traditional | Multiple versions | See notes |

## Commercial Base Recipes (Exact recipes not published - proprietary)

These are studio staples where the exact recipe is unknown but properties are documented:

| Name | Supplier | Type | Notes |
|------|----------|------|-------|
| Lucid Clear | Laguna LG-27 | Clear | See `laguna/README.md` |
| Jensen Blue | Aardvark CTG 04 | Blue | See `aardvark/README.md` |
| Aegean Blue | Aardvark CTG 21 | Blue | See `aardvark/README.md` |
| Tea Dust Black | Aardvark TC-104 | Dark/Tea Dust | See `aardvark/README.md` |
| Tom Coleman Clear | Aardvark TC-103 | Clear | Base for color additions |

## Commercial Cross-References

### Laguna Clay Company
| Code | Name | Studio Match |
|------|------|--------------|
| LG-1 | TIMOKU | Tenmoku family |
| LG-10 | MINT ICE CELADON | Celadon family |
| LG-14 | GREY BLUE CELADON | Celadon family |
| LG-22 | PACIFIC CELADON | Celadon family |
| LG-27 | LUCID CLEAR | Lucid Clear |

**Source:** https://www.lagunaclay.com/collections/glaze-10

### Aardvark Clay & Supply
| Code | Name | Studio Match |
|------|------|--------------|
| CTG 04 | JENSEN BLUE | Jensen Blue |
| CTG 07 | TENMOKU #1 | Tenmoku family |
| CTG 12 | CHUN (BASE) | Chun Blue family |
| CTG 21 | AEGEAN BLUE | Aegean Blue |
| TC-103 | Clear Glaze Base | Tom Coleman Clear |
| TC-104 | Tea Dust Black | Tea Dust |

**Source:** https://aardvarkclay.com/pdf/pricing/Cone%2010%20Glazes.pdf

## Custom Recipes

| Name | Creator | Type | Documented |
|------|---------|------|------------|
| Froggy | Studio | Green | No - studio-specific |
| Toady | Studio | Green | No - studio-specific |
| Larry's Grey | Studio | Grey | No - community recipe, name unknown |
| Long Beach Black | Studio | Black | No - studio-specific |
| Honey Luster | Studio | Luster | No - studio-specific |

## Documentation Template

Use this template for new recipes:

```yaml
name: Recipe Name
source: Original source/creator
cone: "10"
atmosphere: reduction
recipe:
  - material: Material Name
    amount: 40
  - material: Second Material
    amount: 25
color: Visual color description
surface: gloss | matt | semi-matt
notes: |
  Application notes, firing quirks, layering suggestions
food_safe: true | false | unknown
tested: true | false
date_documented: YYYY-MM-DD
```

## Sources

- Glazy.org - Community recipe database
- John Britt books ("The Complete Guide to High-Fire Glazes", "The Complete Guide to Mid-Range Glazes")
- Ceramic Arts Network (ceramicartsnetwork.org/ceramic-recipes)
- Digitalfire (digitalfire.com) - Technical reference
- Studio development and testing

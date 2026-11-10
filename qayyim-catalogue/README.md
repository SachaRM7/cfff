# Catalogue Qayyim : sélection et carte avec QR code

Les 217 produits publics de https://qayyim.fr, rangés en 9 rayons et 37 sous-catégories.

| Fichier | Contenu |
|---|---|
| `data/catalogue.csv` | Le catalogue rangé (rayon, sous-catégorie, produit, prix public, variantes, stock, référence, lien). S'ouvre dans Excel (séparateur `;`). |
| `data/catalogue.json` | Les mêmes données, utilisées par la page. |
| `index.html` + `img/` | La page complète : choix des produits, carte de visite 85 × 55 mm avec QR code, page client ouverte par le QR code. Fonctionne aussi hébergée ailleurs (Netlify, GitHub Pages…) : déposez le dossier tel quel. |
| `src/page.html` | Source de la page (le script y insère les données). |
| `scripts/build_catalogue.py` | Récupère à nouveau le catalogue sur qayyim.fr et régénère tout. |

## Rayons

Livres (115) · Jeux éducatifs (16) · Musc & senteurs (26) · Miel & alimentation (12) · Gamme nigelle (8) · Soins & hygiène (16) · Médecine prophétique (6) · Prière & dévotion (15) · Omra & Hajj (3)

## Mettre à jour le catalogue

```
python3 scripts/build_catalogue.py
```

Nécessite Python 3 et Pillow (`pip install pillow`). Les données viennent de l'API publique WooCommerce du site (`/wp-json/wc/store/v1/products`).

## Le code dans le QR

Le lien du QR code se termine par `#c-…` : c'est la liste des produits cochés, codée selon leur position dans `catalogue.json` (triés par identifiant WooCommerce). Les nouveaux produits s'ajoutent à la fin, donc les cartes déjà imprimées restent valables tant qu'aucun produit n'est supprimé du site. Si des produits disparaissent, la mise à jour décale les positions : il faudra alors refaire les QR codes.

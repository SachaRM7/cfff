# Catalogue Qayyim : sélection et carte avec QR code

Les 217 produits publics de https://qayyim.fr, rangés en 9 rayons et 37 sous-catégories.

| Fichier | Contenu |
|---|---|
| `data/catalogue.csv` | Le catalogue rangé (rayon, sous-catégorie, produit, prix public, variantes, stock, référence, lien). S'ouvre dans Excel (séparateur `;`). |
| `data/catalogue.json` | Les mêmes données, utilisées par la page. |
| `index.html` + `img/` | La page complète, publiée sur GitHub Pages : https://sacharm7.github.io/cfff/ . Elle sert à choisir les produits et à changer leurs prix si besoin. Elle crée la carte de visite 85 × 55 mm avec son QR code, et affiche la page client ouverte par le QR code. |
| `src/page.html` | Source de la page (le script y insère les données). |
| `scripts/build_catalogue.py` | Récupère à nouveau le catalogue sur qayyim.fr et régénère tout. |

## Rayons

Livres (115) · Jeux éducatifs (16) · Musc & senteurs (26) · Miel & alimentation (12) · Gamme nigelle (8) · Soins & hygiène (16) · Médecine prophétique (6) · Prière & dévotion (15) · Omra & Hajj (3)

## Mise en ligne (GitHub Pages)

Le site est dans le dossier `docs/`. Dans le dépôt sur GitHub : Settings → Pages → Source « Deploy from a branch » → branche `claude/qayyim-product-catalog-qr-3fdvjy`, dossier `/docs` → Save. Avec un compte GitHub gratuit, le dépôt doit être public.

## Mettre à jour le catalogue

```
cd docs
python3 scripts/build_catalogue.py
```

Nécessite Python 3 et Pillow (`pip install pillow`). Les données viennent de l'API publique WooCommerce du site (`/wp-json/wc/store/v1/products`).

## Le code dans le QR

Le lien du QR code se termine par `#c-…` (ou `#p-…` quand les prix sont affichés). Il contient la liste des produits cochés, le nom, le téléphone et les prix modifiés (`-x…`). La liste des produits est, codée selon leur position dans `catalogue.json` (triés par identifiant WooCommerce). Les nouveaux produits s'ajoutent à la fin, donc les cartes déjà imprimées restent valables tant qu'aucun produit n'est supprimé du site. Si des produits disparaissent, la mise à jour décale les positions : il faudra alors refaire les QR codes.

<div align="center">

# 🚀 AstroBench

### Benchmark de manipulation d’objets en flottement libre

**Saisir un objet en mouvement et le maintenir après le contact.**

[🌐 Site web](https://astroup.com/astrobench/) · [📖 Spécification (anglais)](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Vidéos](https://astroup.com/astrobench/#videos) · [🐛 Signalements](https://github.com/Brickkkkkk/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | **Français** | [Deutsch](README.de.md)

[![CI](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Protocol](https://img.shields.io/badge/Protocol-0.1_draft-orange)](docs/protocol.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="Un bras robotique à base fixe approche une bobine flottant librement dans une cabine. Cliquer pour voir les vidéos." width="760"></a>

</div>

## 🪐 Qu’est-ce qu’AstroBench ?

AstroBench étudie la manipulation d’objets en flottement libre par un bras robotique à base fixe dans une cabine sans gravité. Sans surface de support, le premier contact peut éloigner l’objet ou le faire tourner. Fermer la pince ne suffit pas : il faut conserver une prise stable.

L’évaluation distingue la **capture**, qui établit une prise stable, du **maintien final**, qui la conserve jusqu’à la fin de l’épisode. La conception générale couvre aussi les mécanismes de cabine, l’insertion, la réorientation et le rangement.

Ce dépôt contient le protocole d’évaluation portable : plans d’épisodes déterministes, évaluation de trajectoires et comptabilisation complète des résultats. Il fonctionne sur CPU avec la bibliothèque standard Python. Un adaptateur d’environnement fournit les trajectoires mesurées ; le paquet ne comprend ni l’environnement complet ni des politiques préentraînées.

### ✨ Points clés

- **Contact et maintien :** vérification du contact des deux doigts avec la cible, de la fermeture mesurée, du mouvement relatif et du maintien continu.
- **Plans reproductibles :** identité des objets, groupes géométriques, conditions de mouvement et protocole liés par les empreintes des épisodes.
- **Couverture explicite :** échecs de tâche, erreurs d’exécution et épisodes manquants restent distincts ; aucune moyenne macro complète pour un plan incomplet.
- **Deux points de vue :** 40 exemples sélectionnés, 20 types d’objets, caméras externe et de cabine.
- **README en sept langues :** la spécification technique détaillée est disponible en anglais et en chinois.

## 🧭 Sommaire

- [🎬 Vidéos des tâches](#watch)
- [⚡ Démarrage rapide](#quickstart)
- [📏 Méthode d’évaluation](#evaluation)
- [🧩 Conception des tâches](#tasks)
- [📊 Expérience de développement](#evidence)
- [🗂️ Structure du dépôt](#layout)
- [🛠️ État de publication](#roadmap)
- [🤝 Contribuer et citer](#contributing)

<a id="watch"></a>

## 🎬 Vidéos des tâches

| Bobine en mouvement | Clé en mouvement | Bobine initialement immobile |
| --- | --- | --- |
| [![Bobine en mouvement](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Clé en mouvement](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Bobine initialement immobile](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

La [galerie interactive](https://astroup.com/astrobench/#videos) permet de chercher un objet, de changer de caméra et de consulter les mesures de mouvement. Elle contient **20 types d’objets · 40 épisodes sélectionnés · 80 vidéos**. Ces exemples ne constituent pas un taux de réussite sur un jeu de test. Les anciennes étiquettes de maintien relèvent du critère utilisé lors de l’enregistrement, distinct de l’évaluateur actuel de maintien final.

<a id="quickstart"></a>

## ⚡ Démarrage rapide

**Prérequis :** Python 3.11+, sans GPU ni dépendances d’exécution autres que la bibliothèque standard. Les commandes ci-dessous utilisent un shell POSIX.

### 1. Installer et vérifier

```bash
git clone https://github.com/Brickkkkkk/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

Les tests vérifient le protocole et les calculs statistiques.

### 2. Générer un plan d’épisodes

```bash
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

Le catalogue fourni est une entrée synthétique de test d’interface, sans ressources physiques associées. Pour une expérience, fournissez des ressources vérifiées avec `object_id`, `asset_sha256`, `geometry_group` et `split`. Le planificateur refuse qu’une ressource ou un groupe géométrique soit partagé entre partitions.

### 3. Évaluer une trajectoire mesurée

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
```

Exportez d’abord `trace.json` depuis l’adaptateur, puis remplacez `EPISODE_ID` par l’identifiant affiché. La trace contient `episode_id`, `spec_hash` et `samples`. Chaque échantillon indique le temps, les forces de chaque doigt sur la cible, la fermeture mesurée, le contact interdit, la sortie de l’espace de travail, les vitesses et la pose relatives. Voir le [contrat des champs (anglais)](docs/protocol.md#trace-and-adapter-contract).

### 4. Agréger les résultats

```bash
python -c 'import json; json.dump([json.load(open("episode-result.json"))], open("results.json", "w"))'
astrobench report plan.json results.json --output report.json
```

Cet exemple rassemble un seul résultat : un plan à plusieurs épisodes sera donc signalé comme incomplet. Pour un rapport complet, incluez tous les résultats prévus pour une même politique/un même checkpoint dans le tableau JSON. La CLI refuse d’écraser les sorties existantes ; utilisez de nouveaux chemins à chaque exécution.

<a id="evaluation"></a>

## 📏 Méthode d’évaluation

Catalogue vérifié → plan enregistré et empreintes d’identité → trajectoire mesurée par l’adaptateur → évaluation de capture/maintien final → réussite, couverture et incertitude. La version publique provisoire est `astrobench.capture-retain/0.1-draft`.

| Paramètre | Valeur |
| --- | --- |
| Durée de l’épisode | 12 s |
| Fenêtre de maintien continu | 1.0 s écoulée selon les horodatages |
| Fréquence nominale / intervalle maximal | 50 Hz / 25 ms |
| Force sur la cible | Au moins 0.5 N par doigt |
| Vitesse relative linéaire / angulaire maximale | 0.02 m/s / 0.2 rad/s |
| Écart relatif maximal de position / orientation | 0.01 m / 0.1 rad |

**Une capture précoce suivie d’une perte n’est pas un succès.** Une fenêtre de maintien valide et continue doit se terminer à l’horizon de l’épisode. Les traces invalides ou tronquées sont rejetées. L’expiration normale du temps de tâche est un échec ; les erreurs d’exécution et épisodes manquants sont comptés séparément.

Le planificateur propose `static`, `drift`, `tumble` et `fast_tumble`. Ces conditions de mouvement sont provisoires, et ne constituent pas un benchmark de généralisation figé. Les seuils nécessitent encore un étalonnage avec l’adaptateur. L’évaluateur vérifie les traces ; l’adaptateur doit vérifier la configuration physique et la correspondance des capteurs.

📖 [Spécification (anglais)](https://astroup.com/astrobench/docs/current/index.html) · [Protocol reference (English)](docs/protocol.md)

<a id="tasks"></a>

## 🧩 Conception des tâches

| Catégorie | Familles | Preuve de réalisation |
| --- | --- | --- |
| Préhension en flottement libre | Capturer et maintenir un objet | Contact bilatéral, fermeture réelle et maintien |
| Interaction avec des mécanismes | Portes, tiroirs, boutons, molettes/vannes, leviers | État articulaire ou course, direction et ordre des étapes |
| Assemblage de précision | Insertion de pions, connecteurs, modules | Alignement, profondeur et mise en place |
| Manipulation d’objets | Réorienter, ranger et fermer | Pose cible ou séquence placement, relâchement et fermeture |

Les 11 familles prévues dépassent la portée des vidéos de préhension et de l’évaluateur public actuels. Les autres familles nécessitent leur propre validation et leurs propres critères. Les partitions officielles d’objets et de mouvements restent à figer.

<a id="evidence"></a>

## 📊 Expérience de développement

Un pilote apparié de 40 épisodes avec un cube compare un checkpoint ACT figé à une référence adaptée par retour d’état : dix positions de développement, deux conditions de mouvement et deux méthodes, sans nouvel entraînement.

| Méthode | Condition initiale | Prise établie | Maintien final |
| --- | --- | --- | --- |
| ACT | Immobile | 8 / 10 | 3 / 10 |
| ACT | En mouvement | 6 / 10 | 0 / 10 |
| Référence par retour d’état | Immobile | 8 / 10 | 8 / 10 |
| Référence par retour d’état | En mouvement | 0 / 10 | 0 / 10 |

Ce pilote utilise un **protocole natif de 15 Hz et 20 secondes**, distinct de l’évaluateur public de 12 secondes. La référence accède à un état privilégié ; tous ses épisodes en mouvement ont atteint une limite de suivi propre au contrôleur. Ses prises statiques surviennent plus tard, laissant moins de temps pour observer le maintien. Il s’agit de diagnostics de développement, pas d’un classement à information égale ni d’un score de généralisation sur 20 objets. Voir [configuration, intervalles et interprétation (anglais)](https://astroup.com/astrobench/docs/current/index.html#pilot).

<a id="layout"></a>

## 🗂️ Structure du dépôt

```text
AstroBench/
├── astrobench/
├── docs/protocol.md
├── examples/catalog.json
├── tests/
├── .github/workflows/
├── README.md
└── README.*.md
```

`astrobench/` : plans, évaluation, agrégation et CLI ; `docs/protocol.md` : contrat des traces ; `examples/` : catalogue synthétique ; `tests/` : tests du protocole et des statistiques ; `.github/workflows/` : CI ; `README.*.md` : guides par langue.

<a id="roadmap"></a>

## 🛠️ État de publication

- [x] Paquet portable de planification, évaluation et agrégation
- [x] Tests du protocole et CI GitHub Actions
- [x] Page et spécification anglais/chinois ; README multilingue
- [x] Vidéos sélectionnées à deux points de vue
- [x] Pilote apparié de développement avec un cube
- [ ] Environnement complet portable et distribution des ressources
- [ ] Partitions d’objets figées et conditions de mouvement étalonnées
- [ ] Évaluation élargie des méthodes de référence et maintien observé sur des durées égales
- [ ] Publication de l’article

La collecte automatique de données, les politiques de démonstration/enseignantes, les chaînes d’entraînement et les jeux de données bruts ne font pas partie de cette publication.

<a id="contributing"></a>

## 🤝 Contribuer et citer

Pour un cas limite de notation ou une interface ambiguë, [ouvrez une issue](https://github.com/Brickkkkkk/AstroBench/issues) avec la version du protocole, une trace minimale reproductible et le résultat attendu. Tout changement de seuil ou de sémantique temporelle doit préciser le versionnement des résultats existants. Exécutez les tests avant de soumettre une PR.

L’article est en cours de révision et n’a pas encore d’identifiant arXiv. En attendant une référence officielle, citez l’URL du dépôt ainsi que le commit exact et la version du protocole utilisés.

Travaux connexes : [Space Robotics Bench](https://arxiv.org/abs/2509.23328).


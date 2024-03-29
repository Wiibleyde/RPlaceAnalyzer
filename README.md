# RPlace Analyzer (for 2017 only)

<img src="./img/rplace-logo.png" alt="drawing" width="100%">

## Sommaire

- [Introduction](#introduction)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Observations](#observations)

RPlace Analyzer est un outil permetttant d'analyser les données de l'événement RPlace 2017. Il permet de visualiser les données de l'événement.

## Installation

Pour installer RPlace Analyzer, il suffit de cloner le dépôt git et d'installer les dépendances.

```bash
pip install -r requirements.txt
```

## Utilisation

Pour utiliser RPlace Analyzer, il suffit de lancer le script `main.py` avec un argument correspondant à l'action que vous souhaitez effectuer.

```bash
python main.py -h
```

## Actions

- `-h` ou `--help` : Affiche l'aide
- `-i` ou `--init` : Initialise les données de l'événement (OBLIGATOIRE AVANT TOUTE AUTRE ACTION (sauf -h))
- `-g` ou `--generate` : Génère l'image finale du RPlace
- `-hm` ou `--heatmap` : Génère la heatmap de l'événement
- `-hi` ou `--histogram` : Génère l'histogramme de l'événement (nombre de pixels placés par heure)
- `-co` ou `--color` : Génère le diagramme des couleurs de l'événement

Et c'est tout !

## Observations

POUR JOEL ICI
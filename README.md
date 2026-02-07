# Nexus Core 🚀

**Nexus Core** est un Hub de jeu futuriste et intelligent conçu pour centraliser votre bibliothèque, surveiller votre matériel en temps réel et optimiser vos performances grâce à l'IA.

![Interface Preview](https://via.placeholder.com/800x450?text=Nexus+Core+HUD)

## ✨ Fonctionnalités Clés

- 🎮 **Bibliothèque Universelle** : Détection automatique des jeux (Steam, Epic, Ubisoft, EA, Battle.net, Riot) et gestion des jeux personnalisés.
- 🤖 **Nexus IA** : Un assistant intelligent (basé sur Llama 3.3) capable de diagnostiquer vos lags et de proposer des optimisations de réglages.
- 📊 **Télémétrie HUD** : Surveillance haute technologie du CPU, GPU, RAM et températures avec lissage des données pour une lecture précise.
- ⚡ **Performance Mode** : Analyse de session en temps réel pour identifier les goulots d'étranglement.
- 🎨 **Interface AAA** : Design Frameless, animations fluides, et thèmes dynamiques (Arctic, Cyberpunk, etc.).

## 🛠 Structure du Projet

- `launcher.py` : Module de démarrage et auto-updater.
- `main.py` : Point d'entrée de l'application principale.
- `/core` : Logique interne (IA, Télémétrie, Base de données).
- `/app_ui` : Interface utilisateur PySide6.
- `/plugins` : Scanners de launchers et outils d'analyse.
- `/assets` : Ressources graphiques et polices.

## 🚀 Installation (Développement)

1. Cloner le dépôt :
```bash
git clone https://github.com/votre-compte/NexusCore.git
```

2. Installer les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancer l'application :
```bash
python launcher.py
```

## 📦 Distribution

Pour compiler l'exécutable final :
```bash
pyinstaller NexusCore.spec
```

---
*Développé par **Foz**. Nexus Core est une interface de nouvelle génération pour les joueurs exigeants.*

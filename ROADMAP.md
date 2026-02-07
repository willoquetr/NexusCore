Ok â voilÃ  une roadmap complÃ¨te que tu peux copier-coller Ã  Codex (ou tâen servir comme spec). Je vais partir sur Python + PySide6 (Qt), app 100% desktop, et une archi plugin-first (scanners de launchers + writers de settings + diagnoseurs).

Inspirations open-source (pour âcomment ils fontâ, pas forcÃ©ment pour copier)

Playnite : meilleure rÃ©fÃ©rence pour agrÃ©gation multi-launchers + jeux custom + plugins (structure mental + connecteurs).

Lutris : intÃ©ressant pour lâidÃ©e âcatalogue + runners + custom gamesâ (moins utile pour Windows, mais bon pour la logique).

Heroic Games Launcher : utile pour comprendre lâapproche âmulti-stores + metadataâ, mÃªme si câest plus orientÃ© web tech.

ð Objectif : sâinspirer des patterns (connecteurs, modÃ¨les de donnÃ©es, import, matching), pas recopier.

Stack technique (ce que Codex doit utiliser)
UI / Desktop

PySide6 (Qt) â fenÃªtres natives, tray icon, bons widgets, facile Ã  packager.

Base de donnÃ©es

SQLite (via SQLAlchemy ou sqlite3 direct)

Migrations : Alembic si SQLAlchemy

TÃ©lÃ©mÃ©trie hardware (Windows)

psutil : CPU/RAM/process.

OpenHardwareMonitor ou LibreHardwareMonitor (via WMI/interop) : tempÃ©ratures, fans, voltages (le plus fiable cÃ´tÃ© âcapteursâ).

On peut faire un petit âbridgeâ local (service) qui lit les capteurs et expose en JSON local si besoin.

Scan des launchers / jeux

Parse des manifests/fichiers :

Steam : libraryfolders.vdf + appmanifest_*.acf (lecture VDF)

Epic : manifests .item (JSON)

Others : souvent registry + dossiers install

Lib utile : vdf (parser Valve VDF) pour Steam.

IA / âassistantâ

Phase 1 : moteur de rÃ¨gles (heuristiques) + arbre de dÃ©cision

Phase 2 : LLM (local ou API) uniquement pour converser et expliquer, mais la dÃ©cision vient de tes rÃ¨gles + tes logs

Stockage âknowledge baseâ : JSON versionnÃ© + tables SQLite

Architecture globale (important)

Codex doit construire Ã§a comme 3 couches :

Core (Domain)

modÃ¨les (Game, Launcher, HardwareSnapshot, Issue, Recommendation, Profile)

rÃ¨gles (diagnostic + recommandations)

bus dâÃ©vÃ©nements (quand un jeu est lancÃ©, quand un snapshot est pris, etc.)

Plugins

scanner_* : dÃ©tecter jeux/launchers

writer_* : appliquer des settings (ini/config)

diagnoser_* : diagnostiquer un problÃ¨me spÃ©cifique (stuttering, surchauffe, VRAM, CPU bottleneck)

App UI

bibliothÃ¨que, dÃ©tails jeu, âperformanceâ, assistant, settings

contrÃ´le du service tÃ©lÃ©mÃ©trie

ROADMAP (par phases) â version âCodex doit faireâ
Phase 0 â Setup & fondations (1â2 jours)

But : scaffolding propre + conventions.

Ã faire

crÃ©er repo + structure dossiers :

/app_ui (PySide6)

/core (domain models + services)

/plugins (scanners/writers/diagnosers)

/data (DB, cache)

/tests

dÃ©finir un format dâID unique pour les jeux (ex: steam:730, epic:Fortnite, custom:hash(path)).

dÃ©finir un schÃ©ma DB SQLite minimal :

games

launchers

game_installs (path, exe, args)

hardware_snapshots (timestamp + metrics)

sessions (game_id, start/end)

issues + recommendations (liÃ©s aux sessions)

Livrable

App sâouvre, DB crÃ©Ã©e, logs ok.

Phase 1 â BibliothÃ¨que de jeux (Steam + Custom) (3â7 jours)

But : ton âMVP launcherâ sans IA.

1A) Plugin scanner Steam

Codex doit

crÃ©er plugins/scanner_steam/

lire libraryfolders.vdf

lire appmanifest_*.acf

produire une liste de GameInstall (nom, appid, chemin install, exe probable si possible)

Notes

Au dÃ©part, juste afficher le jeu et son chemin.

Lâexe nâest pas toujours trivial : tu peux stocker âinstall dirâ et demander Ã  lâutilisateur de choisir lâexe (une fois).

1B) Custom games

Codex doit

implÃ©menter âAdd custom pathâ :

choisir un exe

nom du jeu

icÃ´ne optionnelle

arguments optionnels

calculer un custom_id stable (hash path + exe)

1C) UI BibliothÃ¨que

Codex doit

liste jeux (recherche + filtre launcher/custom)

fiche jeu (path, exe, bouton Launch, bouton âSettings / Optimizeâ)

Livrable

Tu vois Steam + jeux custom dans la mÃªme bibliothÃ¨que

Tu peux lancer un jeu custom

Phase 2 â Service de tÃ©lÃ©mÃ©trie + âsessions de jeuâ (4â10 jours)

But : enregistrer lâÃ©tat hardware toutes les X minutes + mode âen jeuâ.

2A) Hardware collector

Codex doit

crÃ©er un module core/telemetry/collector.py

collecter :

CPU usage (global + per core)

RAM used / available

top process CPU/RAM

GPU usage / VRAM / temp (via Libre/OpenHardwareMonitor bridge)

disk I/O (optionnel)

Ã©crire snapshot en SQLite

2B) Game session tracking

Codex doit

quand lâutilisateur clique âLaunchâ :

crÃ©er une session sessions(start_time)

passer le collector en mode âhigh frequencyâ (ex: toutes les 2â5 sec)

quand le process se ferme :

terminer session end_time

repasser en mode normal (ex: 2â5 minutes)

2C) UI âPerformanceâ

Codex doit

page par session :

max temp GPU/CPU

VRAM peak

CPU peak

âspikes dÃ©tectÃ©sâ (simple)

export JSON de session

Livrable

tu lances un jeu â la session se log

tu vois les pics de temp / usage aprÃ¨s

Phase 3 â Moteur de diagnostic (sans LLM) (7â14 jours)

But : ton app commence Ã  âcomprendreâ un problÃ¨me.

3A) DÃ©finir un modÃ¨le âIssueâ

Codex doit

crÃ©er Issue (type, severity, evidence, confidence)

crÃ©er Recommendation (action, risk, reversible, steps)

3B) 10 rÃ¨gles âgoldenâ stuttering/instabilitÃ©

Codex doit implÃ©menter des heuristiques, par exemple :

GPU temp Ã©levÃ©e + baisse de frÃ©quence â throttling probable

VRAM proche max + stutters â textures trop hautes / leak / rÃ©solution

CPU 1 core saturÃ© + GPU sous-utilisÃ© â CPU bound

RAM saturÃ©e + pagefile â swap

Disk I/O spikes â streaming assets

Chaque rÃ¨gle produit :

Issue + evidence (ex: âGPU temp 88Â°C + clock drop -15% pendant 40sâ)

Recommendations (limiter FPS, baisser textures, activer DLSS/FSR, ombres, distance, etc.)

3C) UI âDiagnoseâ

Codex doit

sur la page session :

liste Issues dÃ©tectÃ©s

recommandations classÃ©es (safe â risky)

bouton âApplyâ si possible (phase 4)

Livrable

sans IA, ton app sort dÃ©jÃ  des diagnostics crÃ©dibles

Phase 4 â âWritersâ : modifier des configs de jeux (2â6 semaines, en parallÃ¨le)

But : appliquer des optimisations rÃ©elles.

4A) Choisir 3 jeux ciblÃ©s (ex: Rust + 2 autres)

Codex doit

crÃ©er un plugin writer_rust/ (ou jeu X)

localiser les fichiers settings (ini/json/registry selon jeu)

parser â modifier â sauvegarder

toujours faire :

backup

validation

revert

4B) âPresetâ + âDiffâ

Codex doit

dÃ©finir des presets : âStable FPSâ, âBalancedâ, âQualityâ

afficher un diff avant dâappliquer (valeurs modifiÃ©es)

Livrable

1â3 jeux oÃ¹ âOptimizeâ change vraiment des settings

Phase 5 â Lâassistant IA (LLM) (1â3 semaines)

But : chat utile, mais pilotÃ© par tes donnÃ©es.

5A) RAG local (simple)

Codex doit

indexer :

les Issues/rÃ¨gles

les recommandations

les fiches jeux (oÃ¹ se trouvent configs, quels settings impactent quoi)

Le LLM ne âdevineâ pas : il rÃ©cupÃ¨re ce que tes rÃ¨gles ont conclu.

5B) Chat âflowâ

Codex doit

si user dit : âstuttering sur Rustâ

demander la session la plus rÃ©cente de Rust

analyser issues

expliquer 2â3 hypothÃ¨ses max

proposer actions test A/B

enregistrer rÃ©sultat user (âÃ§a a amÃ©liorÃ© / pas du toutâ)

Livrable

chat qui guide comme un tech support intelligent, basÃ© sur preuves

Phase 6 â Polishing produit (continu)

Tray icon + notifications (âGPU trop chaud pendant sessionâ)

Auto-detect de nouveaux jeux

Import/export profils

ThÃ¨mes UI

Crash reporting local (optionnel)

Installer Windows + auto-update (plus tard)

Plugins Ã  dÃ©velopper (liste claire pour Codex)
Scanners

scanner_steam (prioritÃ© 1)

scanner_epic (prioritÃ© 2)

scanner_registry_uninstall (fallback)

scanner_custom (obligatoire)

Telemetry

collector_psutil

collector_hardwaremonitor (temp GPU/CPU etc.)

Diagnosers

diagnoser_stutter

diagnoser_thermal_throttle

diagnoser_vram_pressure

diagnoser_cpu_bound

Writers

writer_rust

writer_game2

writer_game3

Ce que tu envoies Ã  Codex (prompt prÃªt)

Tu peux lui coller Ã§a :

âConstruis une application desktop Windows en Python avec PySide6. Architecture plugin-first. Phase 1: scanner Steam + custom games + UI bibliothÃ¨que. Phase 2: tÃ©lÃ©mÃ©trie (psutil + Libre/OpenHardwareMonitor) avec SQLite + sessions. Phase 3: moteur de rÃ¨gles pour diagnostiquer stuttering (issues + recommendations). Phase 4: writer pour 1 jeu (Rust) avec backup/revert. Structure /core /plugins /app_ui /tests. Aucun web UI.â
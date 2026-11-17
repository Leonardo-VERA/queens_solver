# ♛ Overlay Queens pour Windows

Tu joues à Queens dans Chrome, tu appuies sur **Ctrl+Alt+Q**, et des cercles
roses ♛ apparaissent **par-dessus le jeu**, sur les cases où mettre les reines.
Tu double-cliques toi-même sur ces cases (les clics traversent l'affichage).

| Raccourci      | Action                                                  |
|----------------|---------------------------------------------------------|
| `Ctrl+Alt+Q`   | capture l'écran sous la souris, résout, affiche les reines |
| `Ctrl+Alt+H`   | cache l'affichage (il se cache aussi tout seul après 30 s) |
| `Ctrl+Alt+X`   | quitte l'outil                                          |

Rien n'est cliqué automatiquement : c'est toi qui joues.

---

## Pourquoi du Python « normal » (et pas Colab / Jupyter / Anaconda)

- **Google Colab / Jupyter en ligne** tournent sur des serveurs ou dans un
  onglet : ils ne voient pas ton écran et ne peuvent rien afficher par-dessus
  Chrome. ❌
- **Anaconda** fonctionnerait, mais c'est très lourd (plusieurs Go) et inutile ici.
- **Python de python.org, installé sur Windows** : léger, et il contient déjà
  ce qu'il faut pour afficher une fenêtre (Tkinter). ✅

> ⚠️ Ton code de dev est dans **WSL (Linux)**. Le Python de WSL ne voit pas
> l'écran Windows : l'outil doit être lancé avec le **Python de Windows**.

---

## 1. Installer Python sur Windows (une seule fois)

1. Va sur <https://www.python.org/downloads/windows/> et télécharge
   **Python 3.12** (ou 3.13), « Windows installer (64-bit) ».
2. Lance l'installateur et **coche « Add python.exe to PATH »** en bas de la
   première fenêtre, puis « Install Now ».
3. Vérifie dans **PowerShell** (touche Windows → tape `PowerShell`) :

   ```powershell
   py --version
   ```

   Ça doit afficher `Python 3.12.x` (ou 3.13).

## 2. Récupérer le projet côté Windows (une seule fois)

Le plus simple est de le cloner depuis GitHub dans un dossier Windows
(par exemple `C:\Users\<toi>\code`).

**Avec Git** (si `git --version` marche dans PowerShell) :

```powershell
mkdir $HOME\code -Force
cd $HOME\code
git clone https://github.com/Leonardo-VERA/queens_solver.git
cd queens_solver
```

**Sans Git** : sur la page GitHub du projet, bouton vert **Code → Download ZIP**,
dézippe-le dans `C:\Users\<toi>\code\queens_solver`, puis dans PowerShell :

```powershell
cd $HOME\code\queens_solver
```

> N'utilise pas directement le dossier WSL (`\\wsl.localhost\...`) : Python
> sous Windows y est lent et l'installation peut échouer.

## 3. Créer l'environnement et installer (une seule fois)

Toujours dans PowerShell, dans le dossier `queens_solver` :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-overlay.txt
```

Si `Activate.ps1` est refusé (« l'exécution de scripts est désactivée ») :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

puis relance la commande `.\.venv\Scripts\Activate.ps1`.

## 4. Lancer l'outil

**Double-clic** sur `tools\lancer_overlay.bat`, ou dans PowerShell :

```powershell
.\.venv\Scripts\Activate.ps1
python tools\queens_overlay.py
```

La console affiche `Prêt.` : laisse-la ouverte (tu peux la réduire).

**Transparence** : l'affichage est à 50 % par défaut. Plus discret ou plus
visible avec `--opacity` (de `0.2` très léger à `1` opaque) :

```powershell
python tools\queens_overlay.py --opacity 0.35
```

## 5. Jouer

1. Ouvre Queens dans Chrome. **La grille doit être entièrement visible**
   (pas coupée par le bas de l'écran).
2. Mets la souris sur l'écran où est le jeu (utile si tu as deux écrans).
3. **Ctrl+Alt+Q** → en moins d'une seconde, les cercles ♛ apparaissent.
4. Double-clique sur chaque cercle. C'est fini 🎉
5. **Ctrl+Alt+H** pour cacher les cercles (ou attends 30 s).

---

## Mettre à jour plus tard

```powershell
cd $HOME\code\queens_solver
git pull
.\.venv\Scripts\Activate.ps1
pip install -r requirements-overlay.txt
```

(Sans Git : retélécharge le ZIP et refais l'étape 3.)

---

## Si ça ne marche pas

**Tester sans raccourci clavier** — capture après 3 s, et garde les images :

```powershell
python tools\queens_overlay.py --once --delay 3 --debug
```

Pendant les 3 secondes, mets Chrome avec la grille au premier plan. Le dossier
`debug\` contient la capture, le résultat (cercles dessinés) et la grille lue :
envoie-les-moi si la grille est mal reconnue.

| Problème | Solution |
|---|---|
| `Raccourci déjà utilisé par un autre programme` | Un autre logiciel utilise Ctrl+Alt+Q/H/X : ferme-le, ou dis-le-moi pour changer les touches. |
| « Grille introuvable » | La grille doit être entière à l'écran ; dézoome Chrome (Ctrl + -) si besoin. |
| Les cercles sont décalés | Envoie les fichiers de `--debug` (souvent lié au zoom Windows sur plusieurs écrans). |
| `py` n'est pas reconnu | Réinstalle Python en cochant « Add python.exe to PATH ». |
| Fermer l'outil | `Ctrl+Alt+X`, ou ferme la fenêtre de console. |

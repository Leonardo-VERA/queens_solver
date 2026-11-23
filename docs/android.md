# ♛ Queens Solver pour Android (bulle par-dessus LinkedIn)

Le même principe que l'overlay Windows (`Ctrl+Alt+Q`), sur le téléphone :
une **bulle ♛** flotte par-dessus les autres applis. Dans Queens (app LinkedIn),
tu touches la bulle → des **cercles roses semi-transparents** montrent où poser
les reines. Tu touches toi-même les cases (tes doigts passent à travers les
cercles). Rien n'est cliqué automatiquement.

- App **perso** : un fichier `.apk` installé à la main, pas de Play Store, gratuit.
- Elle utilise **le même code Python** que l'app Streamlit et l'outil PC
  (`src/queens`), embarqué dans l'app grâce à Chaquopy.
- Testée à la compilation ; à tester sur le téléphone (Android 16, MagicOS).

---

## 1. Installer l'app sur le téléphone

L'APK déjà compilé est ici (ouvre ce chemin dans l'Explorateur Windows) :

```
\\wsl.localhost\Ubuntu\home\leonardo\code\perso\queens_solver\android\QueensSolver.apk
```

1. **Copie `QueensSolver.apk` sur le téléphone** : câble USB (mode
   « Transfert de fichiers ») vers le dossier *Download*, ou envoie-le-toi par
   Google Drive / mail.
2. Sur le téléphone, ouvre **Fichiers → Download → QueensSolver.apk**.
3. Android demande d'**autoriser l'installation d'applis inconnues** pour l'appli
   Fichiers (ou Drive) : autorise, puis reviens et touche **Installer**.
4. MagicOS peut afficher un avertissement (« appli non vérifiée », analyse de
   sécurité) : choisis **Installer quand même** / **Continuer l'installation**.

L'icône violette ♛ **Queens Solver** apparaît dans tes applis.

## 2. Activer la bulle

1. Ouvre **Queens Solver** → **Activer la bulle ♛**.
2. **Première fois seulement** : Android ouvre « Afficher par-dessus d'autres
   applis » (sur Honor : *Fenêtres flottantes* / *Afficher au-dessus*) →
   active **Queens Solver**, reviens dans l'app et retouche **Activer la bulle**.
   - Si l'interrupteur est **grisé** (« Contrôlé par un paramètre restreint ») :
     c'est la protection d'Android pour les applis installées hors Play Store.
     Touche une fois l'interrupteur grisé (un message s'affiche → OK), puis
     touche **ⓘ** (ou *Paramètres → Applis → Queens Solver*) → menu **⋮** en
     haut à droite → **Autoriser les paramètres restreints** → code/empreinte.
     Reviens et active l'interrupteur, il n'est plus grisé.
3. Autorise les **notifications** (affiche « Queens Solver actif »).
4. Android demande ce que tu veux partager → **Écran entier** → **Démarrer**.
   (C'est une sécurité d'Android : il le redemande à chaque activation.)
5. L'app se met en arrière-plan, la bulle ♛ apparaît sur le bord de l'écran.

## 3. Jouer

1. Ouvre **LinkedIn → Queens**. La **grille doit être entièrement visible**.
2. Touche la **bulle ♛** (elle affiche « … » pendant ~1 s).
3. Les cercles apparaissent sur les bonnes cases → touche-les deux fois chacune.
4. Retouche la bulle pour cacher les cercles (ils se cachent seuls après 30 s).

- **Déplacer la bulle** : fais-la glisser.
- **Arrêter** : bouton *Arrêter* dans l'app, ou *Arrêter* dans la notification.
- Si tu **verrouilles le téléphone**, Android coupe la capture : la bulle
  disparaît, réactive-la depuis l'app.

---

## Si ça ne marche pas

| Problème | Solution |
|---|---|
| « Grille introuvable » | La grille doit être entière à l'écran (fais défiler la page). |
| La capture est noire / toujours « introuvable » | Fais une capture d'écran normale (Power + Volume bas) sur Queens : si elle est noire, LinkedIn bloque les captures et l'app ne peut pas voir la grille. |
| Les cercles sont décalés | Fais une capture d'écran **avec les cercles affichés** et envoie-la-moi. |
| Mauvaise grille / mauvaises cases | Cache les cercles, fais une capture d'écran de la grille et envoie-la-moi. |
| La bulle disparaît toute seule | MagicOS ferme les applis en arrière-plan : *Paramètres → Batterie → Lancement des applis → Queens Solver → Gérer manuellement* (tout activer). |
| « Chargement de Python… » | Au premier lancement Python s'installe (quelques secondes) : réessaie. |

---

## Recompiler l'app soi-même (optionnel)

L'APK ci-dessus est compilé depuis WSL. Pour le recompiler sur Windows :

1. Installe **Android Studio** (<https://developer.android.com/studio>).
2. Installe **Python 3.10** pour Windows (python.org, « Windows installer
   (64-bit) » de la dernière 3.10) : Chaquopy en a besoin pour préparer
   numpy/OpenCV, qui n'existent pour Android qu'en Python 3.10.
3. Android Studio → **Open** → le dossier `android/` du projet.
4. Téléphone branché en USB avec le **débogage USB** activé
   (*À propos du téléphone* → 7 touches sur *Numéro de build* →
   *Options pour les développeurs* → *Débogage USB*) → bouton ▶ **Run**.

En ligne de commande : `gradlew.bat assembleDebug` dans `android/` →
`android/app/build/outputs/apk/debug/app-debug.apk`.

> Un APK compilé sur une autre machine n'a pas la même signature : désinstalle
> d'abord l'ancienne version de l'app avant d'installer la nouvelle.

### Voir les erreurs (débogage USB)

```bash
adb logcat -s QueensService python.stderr python.stdout
```

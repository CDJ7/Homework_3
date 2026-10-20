# Readings 5 Presentation: From Research to a Crime-Scene Robot Dog

**Connor Jarrett · ENGR 6010, AI in Robotics · Readings 5**

This is an interactive Python presentation (Streamlit) that explains why each of my four Readings 5
sources matters for our crime-scene Unitree Go2 project. Each source has a slide with a small live
demo. The same program also exports a normal PowerPoint deck to `output/Readings5_Presentation.pptx`.

Everything runs on **Windows 10/11 in VS Code** with plain `pip`. You don't need Linux, WSL, Docker, a robot,
or the real Unitree SDK.

| Slide | Content | Live demo |
|---|---|---|
| 0 | Title | – |
| 1 | The project in one picture | Pipeline diagram tagged by source |
| 2 | Hwangbo et al. (2019) | Toy actuator network vs. ideal and analytical models, with a delay slider |
| 3 | Gurram et al. (2024) survey | Domain randomization on a toy push-cart, with friction, mass and motor-strength sliders |
| 4 | Kine2Go dataset | Downloads one `motion.npy`, or falls back to a synthetic sample, then plots joints, feet, footfalls and a stick figure |
| 5 | unitree_sdk2_python | Mock SDK: LowState → network → LowCmd loop, plus a stain map driving `Move(vx, vy, vyaw)` |
| 6 | How the four fit together | Summary table + next steps |
| 7 | References (APA) | – |

All toy models and synthetic data are labelled on screen. None of the demo numbers are results from the papers.

---

## Windows setup (step by step)

### 1. Install Python 3.11
Download **Python 3.11** from <https://www.python.org/downloads/windows/>. When the installer opens,
**tick "Add python.exe to PATH"**, then click *Install Now*.

### 2. Open the folder in VS Code
1. Unzip `readings5_presentation.zip`.
2. In VS Code, use **File → Open Folder…** and choose the `readings5_presentation` folder.
3. Install the **Python** extension (by Microsoft) from the Extensions panel (`Ctrl+Shift+X`).

### 3. Create the virtual environment and install packages
Open a terminal in VS Code (**Terminal → New Terminal**) and run:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If PowerShell says *"running scripts is disabled on this system"*, run this once, then try `activate` again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Next, press `Ctrl+Shift+P`, choose **Python: Select Interpreter**, and pick the `.venv` interpreter.

### 4. Run it

```powershell
streamlit run app.py          # opens the presentation in your browser
python export_pptx.py         # rebuilds output\Readings5_Presentation.pptx
```

You can also:
- double-click **`run_presentation.bat`** or **`export_pptx.bat`**, or
- in VS Code, open **Run and Debug** (`Ctrl+Shift+D`) and pick **"Run presentation (Streamlit)"** or
  **"Export PowerPoint"**.

To check that everything works, run `python tests/smoke_test.py`. It runs every demo, times it, and renders every slide.

### Presenting
- Use the **◀ Previous / Next ▶** buttons, or the **← / →** arrow keys (PageUp and PageDown also work).
  When a slider has focus, the arrow keys move the slider, so click an empty part of the page first.
- The sidebar (the **>** at the top left) has *Jump to slide* and an **Export to PowerPoint** button
  that builds the deck and gives you a download link.
- Each slide has a **Speaker notes** expander at the bottom.
- In the browser, `Ctrl` + `+` makes everything bigger on a projector.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `activate` is blocked: "running scripts is disabled" | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then reopen the terminal. You can also use Command Prompt and run `.venv\Scripts\activate.bat`. |
| `py` is not recognized | Python wasn't added to PATH. Re-run the installer, choose *Modify*, and tick "Add Python to environment variables". Or use the full path, e.g. `C:\Users\<you>\AppData\Local\Programs\Python\Python311\python.exe -m venv .venv`. |
| **Port 8501 already in use** | Another Streamlit is still running. Close its terminal, or run on another port: `streamlit run app.py --server.port 8502`. |
| **Kine2Go download fails** (no internet, firewall, proxy, timeout) | Nothing to do. The app **falls back automatically** to the bundled synthetic sample and shows a red "SYNTHETIC SAMPLE" badge. When a download works, the file is cached in `data/kine2go_cache/` and reused offline after that. |
| `pip install` errors | Make sure the venv is active (the prompt starts with `(.venv)`) and that you are using Python 3.11 (`python --version`). Then run `python -m pip install --upgrade pip` and install again. Behind a school proxy, try `pip install --proxy http://<proxy>:<port> -r requirements.txt`. |
| `streamlit` is not recognized | The venv isn't active. Run `.venv\Scripts\activate` first, or use `python -m streamlit run app.py`. |
| The PPTX won't save | Close `Readings5_Presentation.pptx` in PowerPoint first. Windows locks open files. |
| A demo looks stale | Press `C` in the browser to clear the cache, then `R` to rerun. You can also restart Streamlit. |

---

## Project layout

```
readings5_presentation/
├── app.py                  Streamlit presentation (run with: streamlit run app.py)
├── content.py              all slide text + speaker notes (shared by app and PPTX)
├── config.py               every setting: paths, theme colours, demo parameters
├── export_pptx.py          builds output/Readings5_Presentation.pptx (python-pptx)
├── mock_unitree.py         offline mock of unitree_sdk2_python (SportClient, LowState, LowCmd)
├── demos/
│   ├── pipeline.py         slide 1 diagram
│   ├── actuator_net.py     slide 2 demo (toy actuator network)
│   ├── domain_rand.py      slide 3 demo (toy push-cart domain randomization)
│   ├── kine2go.py          slide 4 demo (download / synthetic fallback + plots)
│   ├── sdk_demo.py         slide 5 demo (mock policy loop + investigation layer)
│   └── style.py            shared matplotlib style
├── data/kine2go_synthetic_sample/motion_SYNTHETIC.npy   bundled SYNTHETIC fallback (not Kine2Go data)
├── output/
│   ├── Readings5_Presentation.pptx   generated deck (14 slides, 16:9)
│   ├── figures/                      every demo figure as PNG (default slider values)
│   └── demo_results.json             numbers measured on the last export run
├── docs/writeup.md         Program Explanation + Results for the Word document
├── tests/smoke_test.py     runs every demo and renders every slide with Streamlit AppTest
├── requirements.txt        pinned versions (Python 3.11, Windows wheels available)
├── run_presentation.bat / export_pptx.bat
└── .vscode/launch.json     "Run presentation (Streamlit)" and "Export PowerPoint"
```

## Notes on honesty and limits
- **Toy models.** The actuator and push-cart demos are small toy simulations that show *why* each
  idea matters. They are not reproductions of the papers.
- **Kine2Go column layout.** My notes give the `(T, 61)` shape, 60 Hz and the foot-position columns
  `36:48`. The other column meanings in `config.KINE2GO_ASSUMED_LAYOUT` are an assumption the app needs
  for plotting, and the slide labels them "assumed". Check the dataset card before relying on them.
- **Mock SDK.** `mock_unitree.py` never opens a socket or talks to hardware. If `unitree_sdk2py`
  happens to be installed, the app shows a green badge but still never sends commands.

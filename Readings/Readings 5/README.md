# Readings 5: Reinforcement Learning and Sim-to-Real Transfer for Quadruped Robots

**Student:** Connor Jarrett
**Course:** ENGR 6010, AI in Robotics

This folder holds everything for Readings 5: the written report and all the code I made for it.

## Contents

| Item | Location |
| --- | --- |
| 📄 Readings 5 write-up (Word) | [`Readings 5.docx`](Readings%205.docx) |
| 🐍 Interactive presentation (code) | [`readings5_presentation/`](readings5_presentation/) |
| 📦 Same code as one download | [`readings5_presentation.zip`](readings5_presentation.zip) |
| 📊 Exported PowerPoint | [`readings5_presentation/output/Readings5_Presentation.pptx`](readings5_presentation/output/Readings5_Presentation.pptx) |
| ✍️ Program Explanation + Results text | [`readings5_presentation/docs/writeup.md`](readings5_presentation/docs/writeup.md) |

## The four sources

1. Hwangbo et al. (2019), *Learning Agile and Dynamic Motor Skills for Legged Robots*, <https://arxiv.org/abs/1901.08652>
2. Gurram, Uttam & Ohol (2024), *Reinforcement Learning for Quadrupedal Locomotion: Current Advancements and Future Perspectives*, <https://arxiv.org/abs/2410.10438v1>
3. Kine2Go dataset (MIMUW Robotics, Hugging Face), <https://huggingface.co/datasets/MIMUW-Robotics/kine2go>
4. unitree_sdk2_python (Unitree Robotics, GitHub), <https://github.com/unitreerobotics/unitree_sdk2_python>

## What the code does

`readings5_presentation/` is a Streamlit presentation that explains why each source matters for our
crime-scene Unitree Go2 project. Each source has a small live demo:

- **Hwangbo:** a toy actuator network beats ideal and analytical actuator models (delay slider).
- **Survey:** domain randomization on a toy push-cart (friction, mass and motor-strength sliders).
- **Kine2Go:** downloads one `motion.npy`, or falls back to a clearly labelled synthetic sample, and plots it.
- **Unitree SDK:** a mock SDK policy loop (LowState → network → LowCmd) and a stain-map investigation
  layer that sends `Move(vx, vy, vyaw)` commands.

It also exports the same slides to PowerPoint.

## Quick start (Windows, VS Code)

```powershell
cd readings5_presentation
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py        # the presentation
python export_pptx.py       # rebuild the PowerPoint
```

See [`readings5_presentation/README.md`](readings5_presentation/README.md) for the full step-by-step
instructions and troubleshooting.

"""
smoke_test.py - quick check that every demo runs fast and every slide renders.

Run from the project folder:  python tests/smoke_test.py
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
import content  # noqa: E402
from demos import actuator_net, domain_rand, kine2go, pipeline, sdk_demo  # noqa: E402

TIME_LIMIT_S = 10.0


def check_demos():
    print("== Demo functions ==")
    checks = [
        ("pipeline", lambda: pipeline.run()),
        ("actuator_net (default delay)", lambda: actuator_net.run(config.ACT_DEFAULT_DELAY_MS)),
        ("actuator_net (0 ms)", lambda: actuator_net.run(0)),
        ("actuator_net (20 ms)", lambda: actuator_net.run(20)),
        ("domain_rand", lambda: domain_rand.run()),
        ("domain_rand (carpet floor)", lambda: domain_rand.run(friction=0.4, mass=1.0, strength=1.0)),
        ("kine2go (offline)", lambda: kine2go.run(download=False)),
        ("kine2go (try download)", lambda: kine2go.run(download=True)),
        ("sdk_demo", lambda: sdk_demo.run()),
    ]
    ok = True
    for name, fn in checks:
        t0 = time.perf_counter()
        out = fn()
        dt = time.perf_counter() - t0
        n_figs = len(out.get("figures", {}))
        status = "OK " if dt < TIME_LIMIT_S and n_figs > 0 else "BAD"
        ok &= status == "OK "
        extra = ""
        if "errors" in out:
            extra = " | RMSE " + ", ".join(f"{k.split(') ')[1]}={v:.2f}" for k, v in out["errors"].items())
        if "live_outcome" in out:
            extra = " | live: " + ", ".join(f"{k.split(' (')[0]}={'pass' if v else 'fail'}"
                                            for k, v in out["live_outcome"].items())
        if "synthetic" in out:
            extra = f" | synthetic fallback={out['synthetic']}"
        print(f"  [{status}] {name:30s} {dt:5.2f} s  {n_figs} figure(s){extra}")
    return ok


def check_app():
    print("== Streamlit slides (AppTest) ==")
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)
    at.run()
    ok = True
    for i in range(len(content.SLIDES)):
        t0 = time.perf_counter()
        if i > 0:
            at.button(key="next_top").click().run()
        errors = [e.value for e in at.exception]
        title = content.SLIDES[i]["title"]
        current = at.session_state["slide"]
        good = not errors and current == i
        ok &= good
        print(f"  [{'OK ' if good else 'BAD'}] slide {i}: {title[:55]:55s} {time.perf_counter() - t0:5.2f} s")
        for e in errors:
            print("      exception:", e)
        # Exercise the interactive widgets on the demo slides
        if content.SLIDES[i]["key"] == "hwangbo":
            at.slider[0].set_value(20).run()
            ok &= not at.exception
            print(f"      slider delay=20 ms -> {'OK' if not at.exception else 'ERROR'}")
        if content.SLIDES[i]["key"] == "survey":
            at.slider[0].set_value(0.45).run()
            at.slider[1].set_value(2.5).run()
            ok &= not at.exception
            print(f"      sliders friction=0.45, mass=2.5 -> {'OK' if not at.exception else 'ERROR'}")
        if content.SLIDES[i]["key"] == "kine2go":
            dl = [b for b in at.button if "download" in b.label.lower()][0]
            dl.click().run()
            ok &= not at.exception
            print(f"      download button -> {'OK' if not at.exception else 'ERROR'}")
        if content.SLIDES[i]["key"] == "sdk":
            at.slider[0].set_value(3).run()
            ok &= not at.exception
            print(f"      inspect policy step 3 -> {'OK' if not at.exception else 'ERROR'}")
    # Previous button works too
    at.button(key="prev_top").click().run()
    ok &= at.session_state["slide"] == len(content.SLIDES) - 2
    return ok


if __name__ == "__main__":
    t_all = time.perf_counter()
    demos_ok = check_demos()
    app_ok = check_app()
    print(f"\nDemos: {'PASS' if demos_ok else 'FAIL'}   Slides: {'PASS' if app_ok else 'FAIL'}   "
          f"({time.perf_counter() - t_all:.1f} s total)")
    sys.exit(0 if demos_ok and app_ok else 1)

# Hustad outreach pipeline.
# Real data lives in data/raw and never enters git. See docs/PRIVACY.md.

PY      ?= python3
DAY     ?= $(shell TZ=America/Chicago date +%F)
PLAN    ?= data/work/plan_with_copy_final.csv
LOG     ?= data/work/send_log.csv

.PHONY: help setup dirs sample content assets thread desk site serve plan copy folder workbook playbook clean check

help:
	@echo "make setup      install python deps"
	@echo "make sample     generate synthetic data and build the desk from it (no real data needed)"
	@echo "make desk       build the desk page for DAY=$(DAY) as an artifact fragment"
	@echo "make site       build the desk page as a standalone document into site/index.html"
	@echo "make serve      serve site/ on http://localhost:8000"
	@echo "make plan       full rebuild: classify, select, scale, calendar, copy, level"
	@echo "make copy       regenerate message copy only (after editing hooks.py or copy_engine.py)"
	@echo "                copy is deterministic: rerunning it must not change a message already sent"
	@echo "make folder     rebuild the day files the scheduled desk reads"
	@echo "make workbook   build the analysis workbook"
	@echo "make content    validate and rebuild the posting calendar"
	@echo "make assets     render post graphics to PNG and carousels to PDF (add FORCE=1)"
	@echo "make thread     pull a replying firm's colleagues forward (dry run; add APPLY=1)"
	@echo "make check      run the invariant checks"
	@echo ""
	@echo "export SUPABASE_URL and SUPABASE_ANON_KEY before make desk/site to sync every tick to a"
	@echo "real database instead of only localStorage. Unset (the default), nothing changes. See"
	@echo "backend/db/README.md to provision one."

setup:
	$(PY) -m pip install -r requirements.txt

# dirs first: a fresh clone has no data/work, because git cannot track an empty directory
dirs:
	@mkdir -p data/raw data/work data/out site

sample: dirs
	$(PY) pipeline/make_sample.py --out data/sample/plan_with_copy_final.csv
	$(PY) pipeline/content_engine.py --sample
	cp data/sample/plan_with_copy_final.csv data/work/plan_with_copy_final.csv
	$(PY) pipeline/build_desk.py --day $$($(PY) -c "import csv;print(next(csv.DictReader(open('data/sample/plan_with_copy_final.csv')))['touch1_date'])") --standalone --out site/index.html
	@echo "built site/index.html from synthetic data. make serve to look at it."

desk: dirs content
	$(PY) pipeline/build_desk.py --day $(DAY)

site: dirs content
	$(PY) pipeline/build_desk.py --day $(DAY) --standalone --out site/index.html

serve:
	$(PY) -m http.server 8000 --directory site

plan: dirs
	$(PY) pipeline/active_accounts.py
	$(PY) pipeline/classify.py
	$(PY) pipeline/scale_plan.py
	$(PY) pipeline/recalendar.py
	$(MAKE) copy

# copy_engine writes plan_with_copy.csv. Promoting it to plan_with_copy_final.csv is a separate
# step on purpose: final is what the desk, the workbook and the OneDrive folder read, so nothing
# reaches Eric's screen until the copy has been regenerated and levelled in full. Skip the promote
# and every downstream build quietly keeps serving yesterday's file.
# content: validate and regenerate the posting calendar after editing content_engine.py
content: dirs
	$(PY) pipeline/content_engine.py

# Render the designed post assets: stat and checklist cards to PNG, carousels to PDF, in the
# house fonts. The page's own Download PNG button is a system-font quick export; this is final.
assets: content
	$(PY) worker/render_assets.py $(if $(FORCE),--force,)

# After a reply lands, pull that firm's colleagues inside 5 business days. See docs/CADENCE.md.
thread: dirs
	$(PY) pipeline/thread_firm.py --log $(LOG) $(if $(APPLY),--apply,)

copy: dirs
	$(PY) pipeline/copy_engine.py
	cp data/work/plan_with_copy.csv data/work/plan_with_copy_final.csv
	$(PY) pipeline/level_calendar.py

folder: dirs
	$(PY) pipeline/build_onedrive.py

workbook: dirs
	$(PY) pipeline/build_workbook.py
	$(PY) pipeline/recalc.py

playbook:
	$(PY) pipeline/build_doc_content.py && node pipeline/build_playbook.js

check: dirs
	$(PY) scripts/check_invariants.py

# Build products only. account_map.json, the change logs and today's storm file also live in
# data/work and are not reproducible from anything in git, so clean leaves them alone.
clean:
	rm -f data/work/master_contacts.csv data/work/plan_targets.csv data/work/plan_with_copy_final.csv
	rm -rf data/out/* site/index.html __pycache__ pipeline/__pycache__

# Image classifier spot-check samples (SL-21)

Sample photos for spot-checking SL-22's `classify_image()` against real-world
images. This is a fixture set for manual evaluation, not a training set, so
there is no train/val/test split.

All images are sourced from Wikimedia Commons under permissive licenses
(CC0 or CC-BY/CC-BY-SA, which allow reuse with attribution) and resized to a
1024px max dimension to keep the repo lightweight.

Re-sourced for Indian origin, since CivicSense targets Indian cities and the
first pass was almost entirely non-Indian (UK, US, Russia, Uruguay, Hong
Kong). Seven of nine replaceable categories now have an India-located photo.

## Shortfall note

Only 1 image per category was sourced for this pass, below the ticket's
5-10 target. Each one was individually verified for category fit and
license on its Wikimedia Commons file page, so quality/licensing is solid,
just quantity is light. Add more per category before relying on this for a
real accuracy read, the current set is enough to prove the spot-check script
and the classifier's plumbing work end to end.

**Not India-located:** `open_manhole` and `damaged_infrastructure` kept
their original non-Indian photos. A reasonable search effort (Wikimedia
Commons, multiple query variants per category, browsing the Manholes
category tree) didn't turn up a clearly-Indian, clearly-licensed,
clearly-matching replacement for these two, so forcing a weak match
seemed worse than flagging the gap here. Worth another look when more
time is available.

`water_leakage`'s original photo was replaced separately: it had a drawn
circle and a text caption baked into the image, unrealistic for a real
citizen upload, independent of the India-origin question.

## Images

| File | Category | Source | Licence |
|---|---|---|---|
| pothole/pothole_bengaluru.jpg | pothole | [Potholes in Bengaluru road](https://commons.wikimedia.org/wiki/File:Potholes_in_Bengaluru_road.jpg) | CC0 |
| open_manhole/open_manhole_new_orleans.jpg | open_manhole | [Open Manhole and Cover Mid-City New Orleans](https://commons.wikimedia.org/wiki/File:Open_Manhole_and_Cover_Mid-City_New_Orleans.jpg) | CC-BY-2.0 |
| garbage/garbage_dump_panvel_mumbai.jpg | garbage | [A burning roadside garbage dump at Panvel Naka near Mumbai](https://commons.wikimedia.org/wiki/File:A_burning_roadside_garbage_dump_at_Panvel_Naka_near_Mumbai.jpg) | CC-BY-SA-4.0 |
| streetlight/streetlight_off_assam.jpg | streetlight | [Street light off](https://commons.wikimedia.org/wiki/File:Street_light_off.jpg) (Goalpara, Assam) | CC-BY-SA-4.0 |
| water_leakage/water_leak_india.jpg | water_leakage | [Water dripping out of an urban water supply pipeline in India](https://commons.wikimedia.org/wiki/File:Water_dripping_out_of_an_urban_water_supply_pipeline_in_India_20120311.jpg) | CC-BY-SA-3.0 |
| electricity_outage/overhead_cables_kolkata.jpg | electricity_outage | [Overhead Communication Cables, Kolkata](https://commons.wikimedia.org/wiki/File:Overhead_Communication_Cables_-_Kolkata_2011-08-29_4821.JPG) | CC-BY-3.0 |
| drainage_sewage/flooding_mumbai_2017.jpg | drainage_sewage | [Flooding in Mumbai, India 2017](https://commons.wikimedia.org/wiki/File:Flooding_in_Mumbai,_India_2017.jpg) | CC-BY-SA-4.0 |
| damaged_infrastructure/damaged_sidewalk_montevideo.jpg | damaged_infrastructure | [Damaged sidewalk in Montevideo](https://commons.wikimedia.org/wiki/File:Damaged_sidewalk_in_Montevideo_-_01.jpg) | CC-BY-SA-4.0 |
| road_obstruction/fallen_tree_borivali_mumbai.jpg | road_obstruction | [A Fallen Tree in Kulupwadi Rd, Borivali](https://commons.wikimedia.org/wiki/File:A_Fallen_Tree_in_Kulupwadi_Rd,_Borivali_(35520292).jpg) | CC-BY-SA-2.0 |
| other/green_landscape_triund.jpg | other | [A green carpet on the top of triund](https://commons.wikimedia.org/wiki/File:A_green_carpet_on_the_top_of_triund.jpg) (Himachal Pradesh) | CC-BY-SA-4.0 |

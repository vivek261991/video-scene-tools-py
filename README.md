Build the docker image:
docker build -t product-api .      

Pre-Process:
docker run -it --rm product-api bash
python frame-extractor.py clip.mp4 --fps 1 -d output_frames/
python scene-grouper.py 
python detect_products_in_scenes.pye

Run the app: 
docker run -it -p 5000:5000 product-api

Build the docker image:
docker build -t product-api-ocr .      

Pre-Process:
docker run -it product-api-ocr bash
docker run -it my-acr bash
python frame-extractor.py clip.mp4 --fps 1 -d output_frames/
python scene-grouper.py 
python detect_products_in_scenes.py

Open a new terminal:
docker ps (grab the container id and name)
docker commit {containerid} {name}

Run the app: 
docker run -it -p 5000:5000 product-api-ocr
python server.py

rm -rf /app/output_frames/*
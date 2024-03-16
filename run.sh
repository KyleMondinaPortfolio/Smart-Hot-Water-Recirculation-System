#!/bin/bash

source .venv/bin/activate
cd frontend
npm run build
cd ..

nohup node server.js > ./output/server.out & echo $! > run.pid
nohup python -u main.py > ./output/prediction.out & echo $! >> run.pid
nohup python -u accel_processor.py > ./output/processor.out & echo $! >> run.pid
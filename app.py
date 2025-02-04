from fastapi import FastAPI, File, UploadFile
import numpy as np
import cv2
import uvicorn
import os
from io import BytesIO
from PIL import Image

app = FastAPI()

def perona_malik_diffusion(image, iterations=20, K=20, lambda_=0.25, option=1):
    if len(image.shape) == 3:  
        diffused = np.zeros_like(image, dtype=np.uint8)
        for i in range(3): 
            diffused[:, :, i] = perona_malik_diffusion(image[:, :, i], iterations, K, lambda_, option)
        return diffused
    else:  
        image = image.astype(np.float32)
        diffused = image.copy()
        
        for _ in range(iterations):
            north = np.roll(diffused, -1, axis=0) - diffused
            south = np.roll(diffused, 1, axis=0) - diffused
            east = np.roll(diffused, -1, axis=1) - diffused
            west = np.roll(diffused, 1, axis=1) - diffused
            
            if option == 1:
                c_n = np.exp(-(north/K)**2)
                c_s = np.exp(-(south/K)**2)
                c_e = np.exp(-(east/K)**2)
                c_w = np.exp(-(west/K)**2)
            else:
                c_n = 1 / (1 + (north/K)**2)
                c_s = 1 / (1 + (south/K)**2)
                c_e = 1 / (1 + (east/K)**2)
                c_w = 1 / (1 + (west/K)**2)
            
            diffused += lambda_ * (c_n * north + c_s * south + c_e * east + c_w * west)
        
        return np.clip(diffused, 0, 255).astype(np.uint8)

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    contents = await file.read()
    image = np.array(Image.open(BytesIO(contents)).convert("RGB"))
    diffused_image = perona_malik_diffusion(image)
    
    output_path = "results/diffused_image.jpg"
    os.makedirs("results", exist_ok=True)
    cv2.imwrite(output_path, cv2.cvtColor(diffused_image, cv2.COLOR_RGB2BGR))
    
    return {"message": "Image processed successfully", "output_path": output_path}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

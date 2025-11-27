import torch
import clip
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def get_image_embedding(image_path: str):
    """
    Returns CLIP embedding for an image.
    """
    image = preprocess(Image.open(image_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model.encode_image(image)
    # Normalize
    embedding = embedding / embedding.norm(dim=-1, keepdim=True)
    return embedding

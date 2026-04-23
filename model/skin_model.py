import os
import random

def predict_skin_lesion(image_path):
    """
    Mock prediction function for Skin Cancer. 
    In a real scenario, this would load skin_model.h5 and predict using TensorFlow/Keras.
    """
    # Simulate a robust prediction based on some random factor
    # For demonstration, we'll randomize between Benign, Malignant, and Non-Cancerous
    classes = [
        ("Malignant", "High", "Please consult a dermatologist immediately. This lesion shows high risk characteristics of melanoma or other skin cancers."),
        ("Benign", "Low", "The lesion appears benign. However, continue to monitor it for any changes in size, shape, or color."),
        ("Non-Cancerous", "Low", "No signs of skin cancer detected. Keep your skin protected from excessive sun exposure.")
    ]
    
    selected_class = random.choice(classes)
    confidence = float(f"{random.uniform(75.0, 99.9):.2f}")
    
    return {
        "prediction": selected_class[0],
        "risk_level": selected_class[1],
        "recommendation": selected_class[2],
        "confidence": confidence
    }

if __name__ == "__main__":
    print(predict_skin_lesion("dummy.jpg"))

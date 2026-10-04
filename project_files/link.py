from models import Model
from recommender import LLM

threshold = 0.6


model = Model('images (1).jpg')
results = model.predict('images (1).jpg')
scores = model.get_results('images (1).jpg')
crop, disease = scores[0][0].split(' ', 1) 
confidence_score = scores[0][1]



if confidence_score >= threshold:
    llm = LLM(crop_name=crop, disease_name=disease)

    if __name__ == "__main__":
        response = llm.generate_response()
        print()
        print()
        print(response)
 
elif confidence_score < threshold:
    print("Confidence score is below the threshold.")   
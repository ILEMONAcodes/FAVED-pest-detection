const RESULT = {
	crop: "Tomato",
	disease: "Early Blight",
	pathogen: "Alternaria solani",
	confidence: 94,
	status: "diseased" as const,
	description:
		"Fungal infection causing dark concentric lesions, typically starting on older lower leaves. Spreads rapidly in warm, humid conditions.",
	steps: [
		"Remove and destroy all visibly infected leaves immediately.",
		"Apply a copper-based fungicide spray every 7–10 days.",
		"Improve airflow by thinning dense canopy foliage.",
		"Water at the base only — keep foliage dry during irrigation.",
		"Monitor neighboring plants daily for early signs of spread.",
	],
	imageUrl:
		"https://images.unsplash.com/photo-1592921870789-04563d55041c?w=375&h=260&fit=crop&auto=format",
	bbox: { top: 22, left: 14, width: 52, height: 48 },
};

export default RESULT;

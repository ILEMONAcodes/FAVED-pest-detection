export type ResultType = {
	confidence: number;
	annotated_image: string;
	crop: string;
	detections_count: number;
	recognized: boolean;
	status: "diseased" | "healthy";
	mode?: DetectionMode;
	disease: string;
	RESULT?: Partial<Record<LanguageType, LanguageResult>>;
	message?: string;
	findings?: FindingType[];
	warnings?: string[];
	review_required?: boolean;
	pipeline_status?: string;
};

export type DetectionMode = "crop" | "pest" | "both";

export type FindingType = {
	type: "pest" | "disease";
	label: string;
	label_key: string;
	crop: string | null;
	count: number;
	max_confidence: number;
	evidence: string[];
};

export type LanguageResult = {
	cause: string;
	description: string;
	more_about: string;
	pathogen: string;
	prevention: [string];
	status: string;
	steps: [string];
};

export type LanguageType = "English" | "Hausa" | "Igbo" | "Yoruba";

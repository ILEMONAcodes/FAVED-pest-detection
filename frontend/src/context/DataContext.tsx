import React from "react";
import { createContext, useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import type { DetectionMode, ResultType, LanguageResult, LanguageType } from "../types/types";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 300; // ~15 minutes at 3s intervals — pad above your real p99

type DataContextTypes = {
	isLoading: boolean;
	setIsLoading: React.Dispatch<React.SetStateAction<boolean>>;
	DiagnoseCrop: () => void;
	imageLoaded: boolean;
	setImageLoaded: React.Dispatch<React.SetStateAction<boolean>>;
	imgUrl: string;
	setImgUrl: React.Dispatch<React.SetStateAction<string>>;
	uploadImage: (file: FileList | null) => void;
	language: LanguageType;
	setLanguage: (language: LanguageType) => void;
	detectionMode: DetectionMode;
	setDetectionMode: (mode: DetectionMode) => void;
	result: ResultType | null;
	setResult: React.Dispatch<React.SetStateAction<ResultType | null>>;
	elapsedSeconds: number;
	loadingError: string | null;
	translationState: { language: LanguageType; status: "error" } | null;
	retryTranslation: () => void;
};

type DataContextProviderProps = {
	children: React.ReactNode;
};

const DataContext = createContext<null | DataContextTypes>(null);

export const DataContextProvider = ({ children }: DataContextProviderProps) => {
	const navigate = useNavigate();
	const [isLoading, setIsLoading] = useState(false);
	const [imageLoaded, setImageLoaded] = useState<boolean>(false);
	const [imgUrl, setImgUrl] = useState("");
	const [language, setLanguage] = useState<LanguageType>("English");
	const [detectionMode, setDetectionMode] = useState<DetectionMode>("both");
	const [selectedFile, setSelectedFile] = useState("");
	const [result, setResult] = useState<ResultType | null>(null);
	const [elapsedSeconds, setElapsedSeconds] = useState(0);
	const [loadingError, setLoadingError] = useState<string | null>(null);
	const [translationState, setTranslationState] = useState<{ language: LanguageType; status: "error" } | null>(null);
	const [translationAttempt, setTranslationAttempt] = useState(0);

	const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);
	const selectLanguage = (nextLanguage: LanguageType) => {
		setTranslationState(null);
		setLanguage(nextLanguage);
	};

	const uploadImage = (file: FileList | null) => {
		if (file == null) {
			return;
		}
		if (!["image/jpeg", "image/png", "image/webp"].includes(file[0].type)) {
			alert("Invalid file type");
			return;
		}
		const imgUrlVal = URL.createObjectURL(file[0]);
		setImgUrl(imgUrlVal);
		setSelectedFile(imgUrlVal);
		setImageLoaded(true);
	};

	async function startDiagnosisJob(file: string): Promise<string> {
		const blobFile = await fetch(file).then((res) => res.blob());
		const formData = new FormData();
		formData.append("file", blobFile, "photo.jpg");
		formData.append("language", language);
		formData.append("mode", detectionMode);

		const res = await fetch(`${API_BASE}/diagnose/start`, {
			method: "POST",
			body: formData,
			headers: { "ngrok-skip-browser-warning": "true" },
		});
		if (!res.ok) {
			throw new Error(`Failed to start diagnosis: ${res.status}`);
		}
		const { job_id } = await res.json();
		return job_id;
	}

	async function pollDiagnosisJob(jobId: string): Promise<ResultType> {
		for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
			const res = await fetch(`${API_BASE}/diagnose/status/${jobId}`, {
				headers: { "ngrok-skip-browser-warning": "true" },
			});
			if (!res.ok) {
				throw new Error(`Status check failed: ${res.status}`);
			}
			const data = await res.json();

			if (data.status === "done") {
				return data.result as ResultType;
			}
			if (data.status === "error") {
				throw new Error(
					data.error || "Diagnosis failed on the server.",
				);
			}
			if (data.status === "not_found") {
				throw new Error("Diagnosis job expired. Please try again.");
			}

			await new Promise((resolve) =>
				setTimeout(resolve, POLL_INTERVAL_MS),
			);
		}
		throw new Error(
			"Diagnosis is taking longer than expected. Please try again.",
		);
	}

	useEffect(() => {
		if (isLoading) {
			document.body.classList.add("overflow-hidden");
		} else {
			document.body.classList.remove("overflow-hidden");
		}

		return () => {};
	}, [isLoading]);

	useEffect(() => {
		const englishRecommendation = result?.RESULT?.English;
		if (!result || !englishRecommendation || language === "English" || result.RESULT?.[language]) {
			return;
		}

		const controller = new AbortController();

		void (async () => {
			try {
				const response = await fetch(`${API_BASE}/recommend/translate/start`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						"ngrok-skip-browser-warning": "true",
					},
					signal: controller.signal,
					body: JSON.stringify({
						language,
						crop: result.crop,
						disease: result.disease,
						recommendation: englishRecommendation,
					}),
				});
				if (!response.ok) throw new Error("Translation request failed");
				const { job_id: jobId } = await response.json();

				for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
					const statusResponse = await fetch(`${API_BASE}/diagnose/status/${jobId}`, {
						signal: controller.signal,
						headers: { "ngrok-skip-browser-warning": "true" },
					});
					if (!statusResponse.ok) throw new Error("Translation status check failed");
					const job = await statusResponse.json();
					if (job.status === "done") {
						const translated = job.result as LanguageResult;
						setResult((currentResult) => {
							if (!currentResult) return currentResult;
						return {
							...currentResult,
							RESULT: { ...currentResult.RESULT, [language]: translated },
						};
						});
						setTranslationState(null);
						return;
					}
					if (job.status === "error" || job.status === "not_found") {
						throw new Error(job.error || "Translation job expired");
					}
					await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
				}
				throw new Error("Translation is taking longer than expected");
			} catch (error: unknown) {
				if (error instanceof Error && error.name === "AbortError") return;
				setTranslationState({ language, status: "error" });
			}
		})();

		return () => controller.abort();
	}, [language, result, translationAttempt]);

	async function DiagnoseCrop() {
		setIsLoading(true);
		setLoadingError(null);
		setElapsedSeconds(0);

		const startTime = Date.now();
		tickRef.current = setInterval(() => {
			setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
		}, 1000);

		try {
			const jobId = await startDiagnosisJob(selectedFile);
			const diagnosis = await pollDiagnosisJob(jobId);
			setResult(diagnosis);
			navigate("/result");
		} catch (error) {
			console.error(error);
			setLoadingError(
				error instanceof Error
					? error.message
					: "Something went wrong. Please try again.",
			);
		} finally {
			if (tickRef.current) {
				clearInterval(tickRef.current);
				tickRef.current = null;
			}
			setIsLoading(false);
		}
	}

	return (
		<DataContext.Provider
			value={{
				isLoading,
				setIsLoading,
				DiagnoseCrop,
				imgUrl,
				setImgUrl,
				imageLoaded,
				setImageLoaded,
				uploadImage,
				setLanguage: selectLanguage,
				language,
				detectionMode,
				setDetectionMode,
				result,
				setResult,
				elapsedSeconds,
				loadingError,
				translationState,
				retryTranslation: () => setTranslationAttempt((attempt) => attempt + 1),
			}}
		>
			{children}
		</DataContext.Provider>
	);
};

export default DataContext;

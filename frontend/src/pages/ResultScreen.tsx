// // import Button from "../components/Button";
// // import RecommendedStep from "../components/RecommendedStep";
// // import { useEffect } from "react";
// // import { useNavigate } from "react-router-dom";
// // // import PRED_RESULT from "../mock/mock";
// // import Badge from "../components/Badge";
// // import { useContext } from "react";
// // import DataContext from "../context/DataContext";
// // import type { LanguageResult, LanguageType } from "../types/types";
// // import Fallback from "../components/Fallback";

// // // const ResultScreen = () => {
// // // 	const navigate = useNavigate();
// // // 	const ctx = useContext(DataContext);
// // // 	const PRED_RESULT = ctx?.result;
// // // 	console.log(PRED_RESULT);
// // // 	if (!PRED_RESULT) {
// // // 		return null;
// // // 	}
// // // 	const RESULT: { English: LanguageResult; Hausa: LanguageResult } =
// // // 		PRED_RESULT.RESULT;

// // // 	// if (!RESULT) {
// // // 	// 	return null;
// // // 	// }

// // // 	// Safely access the nested language property
// // // 	const currentLang: LanguageType = (ctx?.language ||
// // // 		"English") as keyof typeof RESULT;
// // // 	const languageResult: LanguageResult =
// // // 		RESULT[currentLang] || RESULT["English"];

// // // 	// Safely access the base64 image
// // // 	const annotatedBase64 = PRED_RESULT?.annotated_image;

// // // 	return (
// // // 		<div className="w-full md:min-h-[calc(100vh-2rem)] flex flex-col p-6 items-center gap-4 grow  overflow-y-auto shrink-0">
// // // 			{PRED_RESULT?.recognized ? (
// // // 				<>
// // // 					<div className="flex flex-col  gap-4 w-full">
// // // 						<div className="image rounded-lg overflow-hidden aspect-4/3 w-full md:aspect-3/1 ">
// // // 							<img
// // // 								src={`data:image/png;base64,${annotatedBase64}`}
// // // 								alt=""
// // // 								className="w-full h-full md:object-cover"
// // // 							/>
// // // 						</div>
// // // 						<div className="w-full flex justify-between items-center gap-4 ">
// // // 							<Badge status={PRED_RESULT.status} />
// // // 							<article>
// // // 								Confidence:{" "}
// // // 								<span className="font-extrabold">
// // // 									{(PRED_RESULT.confidence * 100).toFixed(2)}%
// // // 								</span>
// // // 							</article>
// // // 						</div>
// // // 					</div>

// // // 					<div className="flex flex-col gap-.5  p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
// // // 						<span className="uppercase text-sm font-semibold text-[#A8D0C5] text-[.8rem]">
// // // 							{PRED_RESULT.crop}
// // // 						</span>
// // // 						<span className="text-3xl font-bold">
// // // 							{PRED_RESULT.disease}
// // // 						</span>
// // // 						<p className="pt-2 text-[#76a599] text-[1rem] ">
// // // 							{languageResult.description}
// // // 						</p>
// // // 					</div>

// // // 					<div className=" cause flex flex-col gap-.5  p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
// // // 						<span className="uppercase text-[#0F6E56] text-md font-bold">
// // // 							The Cause
// // // 						</span>
// // // 						<p className="pt-2 text-[#76a599] text-[1rem]">
// // // 							{languageResult.cause}
// // // 						</p>
// // // 					</div>

// // // 					<div className="recommended flex flex-col rounded-2xl overflow-hidden w-full">
// // // 						<div className="w-full bg-[#0F6E56] text-white p-4">
// // // 							<h3 className="text-md font-bold uppercase">
// // // 								Recommended Steps
// // // 							</h3>
// // // 						</div>
// // // 						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl ">
// // // 							{languageResult.steps.map((step, idx) => (
// // // 								<RecommendedStep
// // // 									step={step}
// // // 									id={idx + 1}
// // // 									key={idx}
// // // 								/>
// // // 							))}
// // // 						</div>
// // // 					</div>

// // // 					<div className="prevent flex flex-col rounded-2xl overflow-hidden w-full">
// // // 						<div className="w-full bg-[#0F6E56] text-white p-4">
// // // 							<h3 className="text-md font-bold uppercase">
// // // 								HOW TO PREVENT
// // // 							</h3>
// // // 						</div>
// // // 						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl ">
// // // 							{languageResult.prevention.map((step, idx) => (
// // // 								<RecommendedStep
// // // 									step={step}
// // // 									id={idx + 1}
// // // 									key={idx}
// // // 								/>
// // // 							))}
// // // 						</div>
// // // 					</div>
// // // 				</>
// // // 			) : (
// // // 				<Fallback
// // // 					message={PRED_RESULT?.message || "No result"}
// // // 					mode={PRED_RESULT?.status == "diseased" ? "default" : ""}
// // // 				/>
// // // 			)}

// // // 			<Button
// // // 				text={
// // // 					ctx?.language === "Hausa"
// // // 						? "Duba wani amfanin gona"
// // // 						: "Scan another Crop"
// // // 				}
// // // 				clickFunction={() => {
// // // 					ctx?.setIsLoading(true);
// // // 					ctx?.setImageLoaded(false);
// // // 					ctx?.setImgUrl("");
// // // 					ctx?.setResult(null);
// // // 					ctx?.setIsLoading(false);
// // // 					navigate("/");
// // // 				}}
// // // 				type="main"
// // // 			/>
// // // 		</div>
// // // 	);
// // // };

// // // export default ResultScreen;

// // const ResultScreen = () => {
// // 	const navigate = useNavigate();
// // 	const ctx = useContext(DataContext);
// // 	const PRED_RESULT = ctx?.result;
// // 	console.log(PRED_RESULT);

// // 	useEffect(() => {
// // 		if (!PRED_RESULT) {
// // 			navigate("/", { replace: true });
// // 		}
// // 	}, [PRED_RESULT, navigate]);

// // 	if (!PRED_RESULT) {
// // 		return null;
// // 	}

// // 	const currentLang: LanguageType = (ctx?.language ||
// // 		"English") as LanguageType;
// // 	const annotatedBase64 = PRED_RESULT?.annotated_image;

// // 	// A recognized-but-healthy detection has no RESULT to show
// // 	const hasRecommendation =
// // 		PRED_RESULT?.recognized && PRED_RESULT?.RESULT != null;

// // 	const languageResult: LanguageResult | null = hasRecommendation
// // 		? PRED_RESULT.RESULT![currentLang] || PRED_RESULT.RESULT!["English"]
// // 		: null;

// // 	return (
// // 		<div className="w-full md:min-h-[calc(100vh-2rem)] flex flex-col p-6 items-center gap-4 grow overflow-y-auto shrink-0">
// // 			{hasRecommendation && languageResult ? (
// // 				<>
// // 					<div className="flex flex-col gap-4 w-full">
// // 						<div className="image rounded-lg overflow-hidden aspect-4/3 w-full md:aspect-3/1">
// // 							<img
// // 								src={`data:image/png;base64,${annotatedBase64}`}
// // 								alt=""
// // 								className="w-full h-full md:object-cover"
// // 							/>
// // 						</div>
// // 						<div className="w-full flex justify-between items-center gap-4">
// // 							<Badge status={PRED_RESULT.status} />
// // 							<article>
// // 								Confidence:{" "}
// // 								<span className="font-extrabold">
// // 									{(PRED_RESULT.confidence * 100).toFixed(2)}%
// // 								</span>
// // 							</article>
// // 						</div>
// // 					</div>

// // 					<div className="flex flex-col gap-.5 p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
// // 						<span className="uppercase text-sm font-semibold text-[#A8D0C5] text-[.8rem]">
// // 							{PRED_RESULT.crop}
// // 						</span>
// // 						<span className="text-3xl font-bold">
// // 							{PRED_RESULT.disease}
// // 						</span>
// // 						<p className="pt-2 text-[#76a599] text-[1rem]">
// // 							{languageResult.description}
// // 						</p>
// // 					</div>

// // 					<div className="cause flex flex-col gap-.5 p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
// // 						<span className="uppercase text-[#0F6E56] text-md font-bold">
// // 							{ctx?.language == "English"
// // 								? "The Cause"
// // 								: "Dalilin"}
// // 						</span>
// // 						<p className="pt-2 text-[#76a599] text-[1rem]">
// // 							{languageResult.cause}
// // 						</p>
// // 					</div>

// // 					<div className="recommended flex flex-col rounded-2xl overflow-hidden w-full">
// // 						<div className="w-full bg-[#0F6E56] text-white p-4">
// // 							<h3 className="text-md font-bold uppercase">
// // 								Recommended Steps
// // 							</h3>
// // 						</div>
// // 						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl">
// // 							{languageResult.steps.map((step, idx) => (
// // 								<RecommendedStep
// // 									step={step}
// // 									id={idx + 1}
// // 									key={idx}
// // 								/>
// // 							))}
// // 						</div>
// // 					</div>

// // 					<div className="prevent flex flex-col rounded-2xl overflow-hidden w-full">
// // 						<div className="w-full bg-[#0F6E56] text-white p-4">
// // 							<h3 className="text-md font-bold uppercase">
// // 								HOW TO PREVENT
// // 							</h3>
// // 						</div>
// // 						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl">
// // 							{languageResult.prevention.map((step, idx) => (
// // 								<RecommendedStep
// // 									step={step}
// // 									id={idx + 1}
// // 									key={idx}
// // 								/>
// // 							))}
// // 						</div>
// // 					</div>
// // 				</>
// // 			) : (
// // 				<Fallback
// // 					message={
// // 						PRED_RESULT?.recognized
// // 							? "Great news — this crop looks healthy! No treatment needed."
// // 							: "No result. Please try again"
// // 					}
// // 					mode={PRED_RESULT?.status === "diseased" ? "default" : ""}
// // 				/>
// // 			)}

// // 			<Button
// // 				text={
// // 					ctx?.language === "Hausa"
// // 						? "Duba wani amfanin gona"
// // 						: "Scan another Crop"
// // 				}
// // 				clickFunction={() => {
// // 					ctx?.setIsLoading(true);
// // 					ctx?.setImageLoaded(false);
// // 					ctx?.setImgUrl("");
// // 					ctx?.setResult(null);
// // 					ctx?.setIsLoading(false);
// // 					navigate("/");
// // 				}}
// // 				type="main"
// // 			/>
// // 		</div>
// // 	);
// // };

// // export default ResultScreen;

// import Button from "../components/Button";
// import RecommendedStep from "../components/RecommendedStep";
// import { useEffect } from "react";
// import { useNavigate } from "react-router-dom";
// import Badge from "../components/Badge";
// import { useContext } from "react";
// import DataContext from "../context/DataContext";
// import type { LanguageResult, LanguageType } from "../types/types";
// import Fallback from "../components/Fallback";

// const ResultScreen = () => {
// 	const navigate = useNavigate();
// 	const ctx = useContext(DataContext);
// 	const PRED_RESULT = ctx?.result;
// 	console.log(PRED_RESULT);
// 	console.log(PRED_RESULT?.message);

// 	useEffect(() => {
// 		if (!PRED_RESULT) {
// 			navigate("/", { replace: true });
// 		}
// 	}, [PRED_RESULT, navigate]);

// 	if (!PRED_RESULT) {
// 		return null;
// 	}

// 	const currentLang: LanguageType = (ctx?.language ||
// 		"English") as LanguageType;
// 	const annotatedBase64 = PRED_RESULT?.annotated_image;

// 	// A recognized-but-healthy detection has no RESULT to show
// 	const hasRecommendation =
// 		PRED_RESULT?.recognized &&
// 		PRED_RESULT?.RESULT != null &&
// 		PRED_RESULT?.confidence >= 0.6;

// 	const languageResult: LanguageResult | null = hasRecommendation
// 		? PRED_RESULT.RESULT![currentLang] || PRED_RESULT.RESULT!["English"]
// 		: null;

// 	return (
// 		<div className="w-full md:min-h-[calc(100vh-2rem)] flex flex-col p-6 items-center gap-4 grow pt-20 md:pt-6 overflow-y-auto shrink-0 lg:grid lg:grid-cols-2 lg:grid-rows-[auto_auto] lg:items-start">
// 			{PRED_RESULT?.recognized && (
// 				<div className="flex flex-col gap-4 w-full lg:col-span-1 lg:self-start">
// 					<div className="image rounded-lg overflow-hidden aspect-4/3 w-full  lg:aspect-4/3">
// 						<img
// 							src={`data:image/png;base64,${annotatedBase64}`}
// 							alt=""
// 							className="w-full h-full md:object-cover"
// 						/>
// 					</div>
// 					<div className="w-full flex justify-between items-center gap-4">
// 						<Badge status={PRED_RESULT.status} />
// 						<article>
// 							{ctx.language == "English"
// 								? "Confidence:"
// 								: "Dogaro da kai:"}{" "}
// 							<span className="font-extrabold">
// 								{(PRED_RESULT.confidence * 100).toFixed(2)}%
// 							</span>
// 						</article>
// 					</div>
// 				</div>
// 			)}

// 			{hasRecommendation && languageResult ? (
// 				<div className="flex flex-col gap-2 lg:col-span-1 lg:gap-6">
// 					<div className="flex flex-col gap-.5 p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
// 						<span className="uppercase text-sm font-semibold text-[#A8D0C5] text-[.8rem]">
// 							{PRED_RESULT.crop}
// 						</span>
// 						<span className="text-3xl font-bold text-[#0f6e56]">
// 							{PRED_RESULT.disease}
// 						</span>
// 						<span className="text-sm italic text-[#31a789]">
// 							{languageResult.pathogen}
// 						</span>
// 						<p className="pt-2 text-[#76a599] text-[1rem]">
// 							{languageResult.description}
// 						</p>
// 					</div>

// 					<div className="cause flex flex-col gap-.5 p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
// 						<span className="uppercase text-[#0F6E56] text-md font-bold">
// 							{ctx?.language == "English"
// 								? "The Cause"
// 								: "Dalilin"}
// 						</span>
// 						<p className="pt-2 text-[#76a599] text-[1rem]">
// 							{languageResult.cause}
// 						</p>
// 					</div>

// 					<div className="recommended flex flex-col rounded-2xl overflow-hidden w-full">
// 						<div className="w-full bg-[#0F6E56] text-white p-4">
// 							<h3 className="text-md font-bold uppercase">
// 								{ctx.language == "English"
// 									? "Recommended Steps"
// 									: "Matakan da aka ba da shawarar bi"}
// 							</h3>
// 						</div>
// 						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl">
// 							{languageResult.steps.map((step, idx) => (
// 								<RecommendedStep
// 									step={step}
// 									id={idx + 1}
// 									key={idx}
// 								/>
// 							))}
// 						</div>
// 					</div>

// 					<div className="prevent flex flex-col rounded-2xl overflow-hidden w-full">
// 						<div className="w-full bg-[#0F6E56] text-white p-4">
// 							<h3 className="text-md font-bold uppercase">
// 								{ctx?.language == "English"
// 									? "HOW TO PREVENT"
// 									: "Yadda za a yi rigakafi"}
// 							</h3>
// 						</div>
// 						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl">
// 							{languageResult.prevention.map((step, idx) => (
// 								<RecommendedStep
// 									step={step}
// 									id={idx + 1}
// 									key={idx}
// 								/>
// 							))}
// 						</div>
// 					</div>
// 				</div>
// 			) : (
// 				// <Fallback
// 				// 	message={
// 				// 		PRED_RESULT?.recognized
// 				// 			? "Great news — this crop looks healthy! No treatment needed."
// 				// 			: "No result. Please try again"
// 				// 	}
// 				// 	mode={PRED_RESULT?.status === "diseased" ? "default" : ""}
// 				// />

// 				<Fallback
// 					message={
// 						PRED_RESULT?.recognized
// 							? PRED_RESULT?.confidence < 0.8
// 								? "We're not confident enough in this result. Please try scanning again with a clearer photo."
// 								: "Great news — this crop looks healthy! No treatment needed."
// 							: "No plant disease was recognized in this image. Please make sure the photo clearly shows a plant leaf, is in focus, well lit, and fills most of the frame, then try again."
// 					}
// 					mode={
// 						PRED_RESULT?.status === "diseased"
// 							? "default"
// 							: PRED_RESULT?.confidence < 0.8
// 								? "unconfident"
// 								: "diseased"
// 					}
// 				/>
// 			)}

// 			<div className="w-full lg:col-start-2 pt-4">
// 				<Button
// 					text={
// 						ctx?.language === "Hausa"
// 							? "Duba wani amfanin gona"
// 							: "Scan another Crop"
// 					}
// 					clickFunction={() => {
// 						ctx?.setIsLoading(true);
// 						ctx?.setImageLoaded(false);
// 						ctx?.setImgUrl("");
// 						ctx?.setResult(null);
// 						ctx?.setIsLoading(false);
// 						navigate("/");
// 					}}
// 					type="main"
// 				/>
// 			</div>
// 		</div>
// 	);
// };

// export default ResultScreen;

import Button from "../components/Button";
import RecommendedStep from "../components/RecommendedStep";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Badge from "../components/Badge";
import { useContext } from "react";
import DataContext from "../context/DataContext";
import type { LanguageResult, LanguageType } from "../types/types";
import Fallback from "../components/Fallback";

const CONFIDENCE_THRESHOLD = 0.8;

const ResultScreen = () => {
	const navigate = useNavigate();
	const ctx = useContext(DataContext);
	const PRED_RESULT = ctx?.result;

	useEffect(() => {
		if (!PRED_RESULT) {
			navigate("/", { replace: true });
		}
	}, [PRED_RESULT, navigate]);

	if (!PRED_RESULT) {
		return null;
	}

	const currentLang: LanguageType = (ctx?.language ||
		"English") as LanguageType;
	const labels = {
		English: { confidence: "Confidence:", cause: "The Cause", steps: "Recommended Steps", prevention: "HOW TO PREVENT", scan: "Scan another Crop", translating: "Translating this recommendation…", translationFailed: "This recommendation could not be translated right now.", retry: "Retry translation" },
		Hausa: { confidence: "Dogaro da kai:", cause: "Dalilin", steps: "Matakan da aka ba da shawarar bi", prevention: "Yadda za a yi rigakafi", scan: "Duba wani amfanin gona", translating: "Ana fassara wannan shawarar…", translationFailed: "Ba a iya fassara wannan shawarar a yanzu ba.", retry: "Sake gwada fassara" },
		Igbo: { confidence: "Ntụkwasị obi:", cause: "Ihe kpatara ya", steps: "Nzọụkwụ ndị a tụrụ aro", prevention: "OTU A GA-ESI GBOCHIE YA", scan: "Nyochaa Osisi Ọzọ", translating: "A na-atụgharị ndụmọdụ a n'asụsụ…", translationFailed: "Enweghị ike ịtụgharị ndụmọdụ a ugbu a.", retry: "Nwalee ntụgharị asụsụ ọzọ" },
		Yoruba: { confidence: "Ìgbẹ́kẹ̀lé:", cause: "Ohun tó fà á", steps: "Àwọn ìgbésẹ̀ tí a dábàá", prevention: "BÍ A ṢE LÈ DÁÀBÒ BO O", scan: "Ṣàyẹ̀wò Irúgbìn Mìíràn", translating: "A ń túmọ̀ ìmọ̀ràn yìí…", translationFailed: "A kò lè túmọ̀ ìmọ̀ràn yìí báyìí.", retry: "Tún gbìyànjú ìtumọ̀" },
	};
	const text = labels[currentLang];
	const annotatedBase64 = PRED_RESULT?.annotated_image;

	// --- Explicit scenario flags ---
	const isRecognized = PRED_RESULT?.recognized === true;
	const isHighConfidence =
		(PRED_RESULT?.confidence ?? 0) >= CONFIDENCE_THRESHOLD;
	const isHealthy = PRED_RESULT?.status === "healthy";
	const isDiseased = PRED_RESULT?.status === "diseased";

	// Scenario 1a: recognized, high confidence, diseased -> full result
	const showFullResult =
		isRecognized && isDiseased && PRED_RESULT?.RESULT != null;

	// Scenario 1b: recognized, high confidence, healthy -> healthy fallback
	const showHealthyFallback = isRecognized && isHighConfidence && isHealthy;

	// Scenario 2: recognized, but low confidence -> unconfident fallback (still show image/badge/confidence)
	const showLowConfidenceFallback =
		isRecognized && !isHighConfidence && PRED_RESULT?.RESULT == null;

	// Scenario 3: not recognized at all -> unrecognized fallback
	const showUnrecognizedFallback = !isRecognized;

	const languageResult: LanguageResult | null = showFullResult
		? PRED_RESULT.RESULT![currentLang] || null
		: null;
	const translationState = ctx?.translationState;
	const reviewText = {
		English: "This guidance uses draft knowledge-base content and needs agronomist review.",
		Hausa: "Wannan shawarar ta dogara da bayanan da ba a gama tantancewa ba; kwararren noma ya kamata ya duba ta.",
		Igbo: "Ndụmọdụ a sitere na ozi a ka na-enyocha; onye ọkachamara n'ọrụ ugbo kwesịrị ịtụle ya.",
		Yoruba: "Ìmọ̀ràn yìí lo ìsọfúnni tí a kò tíì fọwọ́ sí; onímọ̀ iṣẹ́ àgbẹ̀ gbọ́dọ̀ ṣàyẹ̀wò rẹ̀.",
	}[currentLang];
	const confidenceWarning = {
		English: "Low confidence. Retake a close, well-lit photo before acting on this result.",
		Hausa: "Ba a da cikakken tabbaci ba. Sake ɗaukar hoto kusa kuma mai haske kafin ka ɗauki mataki.",
		Igbo: "Ntụkwasị obi adịghị elu. Biko see foto dị nso ma nwee ezigbo ìhè tupu i mee ihe.",
		Yoruba: "Ìgbẹ́kẹ̀lé kò ga tó. Jọ̀wọ́ tún ya fọ́tò tó sún mọ́lé tí ó sì mọ́lẹ̀ dáadáa kí o tó gbé ìgbésẹ̀.",
	}[currentLang];

	return (
		<div className="w-full md:min-h-[calc(100vh-2rem)] flex flex-col p-6 items-center gap-4 grow pt-20 md:pt-6 overflow-y-auto shrink-0 lg:grid lg:grid-cols-2 lg:grid-rows-[auto_auto] lg:items-start">
			{isRecognized && (
				<div className="flex flex-col gap-4 w-full lg:col-span-1 lg:self-start">
					<div className="image rounded-lg overflow-hidden aspect-4/3 w-full lg:aspect-4/3">
										<img
											src={`data:image/jpeg;base64,${annotatedBase64}`}
							alt=""
							className="w-full h-full md:object-cover"
						/>
					</div>
					<div className="w-full flex justify-between items-center gap-4">
						<Badge status={PRED_RESULT.status} />
						<article>
							{text.confidence}{" "}
							<span className="font-extrabold">
								{(PRED_RESULT.confidence * 100).toFixed(2)}%
							</span>
						</article>
					</div>
				</div>
			)}

			{showFullResult && languageResult ? (
				<div className="flex flex-col gap-2 lg:col-span-1 lg:gap-6">
					<div className="flex flex-col gap-.5 p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
						<span className="uppercase text-sm font-semibold text-[#A8D0C5] text-[.8rem]">
							{PRED_RESULT.crop}
						</span>
						<span className="text-3xl font-bold text-[#0f6e56]">
							{PRED_RESULT.disease}
						</span>
						{PRED_RESULT.findings && PRED_RESULT.findings.length > 0 && (
							<ul className="flex flex-col gap-2 pt-2">
								{PRED_RESULT.findings.map((finding) => (
									<li
										key={finding.label_key}
										className="flex flex-wrap justify-between gap-x-3 gap-y-1 border-t border-[#A8D0C5] pt-2 text-sm text-[#315f53]"
									>
										<span className="font-semibold">
											{finding.label} ({finding.type})
										</span>
										<span>
											{(finding.max_confidence * 100).toFixed(1)}%
											{finding.count > 1 ? ` · ${finding.count} detections` : ""}
										</span>
									</li>
								))}
							</ul>
						)}
						<span className="text-sm italic text-[#31a789]">
							{languageResult.pathogen}
						</span>
						{PRED_RESULT.review_required && (
							<p className="rounded-md border border-amber-300 bg-amber-50 p-2 text-sm text-amber-900">
								{reviewText}
							</p>
						)}
						{PRED_RESULT.warnings?.map((warning) => (
							<p key={warning} className="rounded-md border border-amber-300 bg-amber-50 p-2 text-sm text-amber-900">
								{warning.startsWith("Low confidence") ? confidenceWarning : warning}
							</p>
						))}
						<p className="pt-2 text-[#76a599] text-[1rem]">
							{languageResult.description}
						</p>
					</div>

					<div className="cause flex flex-col gap-.5 p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full">
						<span className="uppercase text-[#0F6E56] text-md font-bold">
							{text.cause}
						</span>
						<p className="pt-2 text-[#76a599] text-[1rem]">
							{languageResult.cause}
						</p>
					</div>

					<div className="recommended flex flex-col rounded-2xl overflow-hidden w-full">
						<div className="w-full bg-[#0F6E56] text-white p-4">
							<h3 className="text-md font-bold uppercase">
								{text.steps}
							</h3>
						</div>
						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl">
							{languageResult.steps.map((step, idx) => (
								<RecommendedStep
									step={step}
									id={idx + 1}
									key={idx}
								/>
							))}
						</div>
					</div>

					<div className="prevent flex flex-col rounded-2xl overflow-hidden w-full">
						<div className="w-full bg-[#0F6E56] text-white p-4">
							<h3 className="text-md font-bold uppercase">
								{text.prevention}
							</h3>
						</div>
						<div className="flex flex-col border border-[#A8D0C5] rounded-b-2xl">
							{languageResult.prevention.map((step, idx) => (
								<RecommendedStep
									step={step}
									id={idx + 1}
									key={idx}
								/>
							))}
						</div>
					</div>
				</div>
			) : (
				<>
					{showHealthyFallback && (
						<Fallback
							message="Great news — this crop looks healthy! No treatment needed."
							mode="healthy"
						/>
					)}
					{showLowConfidenceFallback && (
						<Fallback
							message="We're not confident enough in this result. Please try scanning again with a clearer photo."
							mode="unconfident"
						/>
					)}
					{showUnrecognizedFallback && (
						<Fallback
							message="No plant disease was recognized in this image. Please make sure the photo clearly shows a plant leaf, is in focus, well lit, and fills most of the frame, then try again."
							mode="unrecognized"
						/>
					)}
					{showFullResult && !languageResult && (
						<div className="w-full rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] p-5 text-[#315f53]">
							<p role="status">
								{translationState?.language === currentLang && translationState.status === "error"
									? text.translationFailed
									: text.translating}
							</p>
							{translationState?.language === currentLang && translationState.status === "error" && (
								<button className="mt-3 font-semibold underline" onClick={ctx?.retryTranslation}>
									{text.retry}
								</button>
							)}
						</div>
					)}
				</>
			)}

			<div className="w-full lg:col-start-2 pt-10">
				<Button
					text={text.scan}
					clickFunction={() => {
						ctx?.setIsLoading(true);
						ctx?.setImageLoaded(false);
						ctx?.setImgUrl("");
						ctx?.setResult(null);
						ctx?.setIsLoading(false);
						navigate("/");
					}}
					type="main"
				/>
			</div>
		</div>
	);
};

export default ResultScreen;

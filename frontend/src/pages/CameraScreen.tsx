import { useContext, useRef } from "react";
import Button from "../components/Button";
import CameraInput from "../components/CameraInput";
import DataContext from "../context/DataContext";
// import { useNavigate } from "react-router-dom";

const CameraScreen = () => {
	const ctx = useContext(DataContext);
	const language = ctx?.language ?? "English";
	const labels = {
		English: {
			title: "Farm AI Vision and Recommendation for Early Disease and Pest Detection",
			photo: "Take Photo",
			upload: "Upload from Gallery",
			diagnose: "Run detection",
			mode: "Detection mode",
			cropMode: "Crop disease",
			pestMode: "Pest",
			bothMode: "Pest + disease",
			another: "Upload another Image",
			tip: "For best results, photograph in natural daylight with the affected leaf filling most of the frame.",
		},
		Hausa: {
			title: "Fasahar Hangen Nesa ta AI da Shawarwari don Gano Cututtuka da Wuri a Noma",
			photo: "Ɗauki Hoto",
			upload: "Loda daga ɗakin ajiyar hotuna",
			diagnose: "Gano Matsalar Amfanin Gona",
			mode: "Nau'in ganowa",
			cropMode: "Cutar amfanin gona",
			pestMode: "Kwaro",
			bothMode: "Kwaro + cuta",
			another: "Sanya wani hoton",
			tip: "Domin samun sakamako mafi kyau, a ɗauki hoton a cikin hasken rana na halitta, tare da sanya ganyen da abin ya shafa ya mamaye mafi yawan sararin hoton.",
		},
		Igbo: {
			title: "Nyocha AI na Osisi na Ndụmọdụ maka Ịchọpụta Ọrịa n'Oge Mbido",
			photo: "See Foto",
			upload: "Bulite Foto",
			diagnose: "Chọpụta Ọrịa Osisi",
			mode: "Ụdị nyocha",
			cropMode: "Ọrịa ihe ọkụkụ",
			pestMode: "Ụmụ ahụhụ",
			bothMode: "Ụmụ ahụhụ + ọrịa",
			another: "Bulite Foto Ọzọ",
			tip: "Maka nsonaazụ kacha mma, see foto n'ìhè anyanwụ, ka akwụkwọ osisi ahụ metụtara jupụta ọtụtụ akụkụ foto ahụ.",
		},
		Yoruba: {
			title: "Ìwádìí AI àti Ìmọ̀ràn fún Ṣíṣàwárí Àrùn Irúgbìn Ní Kutukutu",
			photo: "Ya Fọ́tò",
			upload: "Gbé Fọ́tò Wá",
			diagnose: "Ṣàyẹ̀wò Irúgbìn",
			mode: "Iru ayẹwo",
			cropMode: "Arun irugbin",
			pestMode: "Kokoro",
			bothMode: "Kokoro + arun",
			another: "Gbé Fọ́tò Mìíràn Wá",
			tip: "Fún àbájáde tó dára jù, ya fọ́tò ní ìmọ́lẹ̀ oòrùn, kí ewé tó ní àrùn gba ọ̀pọ̀ jù lọ àyè fọ́tò náà.",
		},
	};
	const text = labels[language];
	const uploadRef = useRef<HTMLInputElement>(null);
	const cameraRef = useRef<HTMLInputElement>(null);
	const detectionModes = [
		{ id: "crop", label: text.cropMode },
		{ id: "pest", label: text.pestMode },
		{ id: "both", label: text.bothMode },
	] as const;

	// const navigate = useNavigate();

	const cameraFunction = () => {
		cameraRef.current?.click();
	};
	const uploadFunction = () => {
		uploadRef.current?.click();
	};

	const fileInputHandler = (file: FileList | null) => {
		ctx?.uploadImage(file);
	};

	return (
		<div className="flex flex-col  gap-4 p-6 items-center md:min-h-[calc(100vh-60px)] overflow-y-auto shrink-0 pt-20 md:pt-6">
			<h2 className=" py-2 text-sm font-semibold text-[#056e56] uppercase">
				{text.title}
			</h2>
			<div className="w-full flex flex-col gap-4 lg:grid lg:grid-cols-[2fr_1fr] lg:grid-rows-2 lg:items-start">
				<CameraInput clickFunction={cameraFunction} />
				<div className="w-full flex flex-col gap-2">
					<fieldset className="w-full">
						<legend className="mb-2 text-sm font-semibold text-[#315f53]">
							{text.mode}
						</legend>
						<div className="grid grid-cols-3 border border-[#a8d0c5] bg-white">
							{detectionModes.map((option) => {
								const selected = ctx?.detectionMode === option.id;
								return (
									<button
										key={option.id}
										type="button"
										aria-pressed={selected}
										onClick={() => ctx?.setDetectionMode(option.id)}
										className={`min-h-12 px-2 py-2 text-xs font-semibold transition-colors sm:text-sm ${selected ? "bg-[#0f6e56] text-white" : "text-[#315f53] hover:bg-[#e9f3ef]"}`}
									>
										{option.label}
									</button>
								);
							})}
						</div>
					</fieldset>
					{!ctx?.imageLoaded ? (
						<>
							<Button
								text={text.photo}
								clickFunction={cameraFunction}
								type="main"
							/>
							<Button
								text={text.upload}
								clickFunction={uploadFunction}
								type="secondary"
							/>
						</>
					) : (
						<>
							<Button
								text={text.diagnose}
								clickFunction={() => {
									ctx?.DiagnoseCrop();
								}}
								type="main"
							/>
							<Button
								text={text.another}
								clickFunction={() => {
									ctx?.setImgUrl("");
									ctx?.setImageLoaded(false);
								}}
								type="secondary"
							/>
						</>
					)}
					{ctx?.loadingError && (
						<p className="rounded-lg border-2 border-red-200 bg-red-50 p-3 text-sm text-red-700">
							{ctx.loadingError}
						</p>
					)}
					<input
						type="file"
						accept="image/*"
						ref={uploadRef}
						className="hidden"
						onChange={(e) => {
							fileInputHandler(e.target.files);
						}}
					/>
					<input
						type="file"
						accept="image/*"
						capture="environment"
						ref={cameraRef}
						className="hidden"
						onChange={(e) => {
							fileInputHandler(e.target.files);
						}}
					/>
				</div>
				<div className="flex gap-3 p-4 rounded-2xl bg-[#f7faf9] border-3 border-[#a8d0c5] w-full h-fit md:items-center lg:self-end lg:items-start">
					<div className="w-fit h-fit">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 640 640"
							className="fill-[#0f6e56] w-7 h-7 md:w-10 md:h-10 lg:w-7 lg:h-7"
						>
							<path d="M320 32C328 32 335.4 36 339.9 42.6L398.7 130L502.1 109.8C509.9 108.3 518 110.7 523.7 116.4C529.4 122.1 531.8 130.2 530.3 138L510 241.3L597.4 300.1C604 304.5 608 312 608 320C608 328 604 335.4 597.4 339.9L510 398.7L530.2 502C531.7 509.8 529.3 517.9 523.6 523.6C517.9 529.3 509.8 531.7 502 530.2L398.7 510L339.9 597.4C335.4 604 328 608 320 608C312 608 304.6 604 300.1 597.4L241.3 510L137.9 530.2C130.1 531.7 122 529.3 116.3 523.6C110.6 517.9 108.2 509.8 109.7 502L130 398.7L42.6 339.9C36 335.4 32 328 32 320C32 312 36 304.6 42.6 300.1L130 241.3L109.8 137.9C108.3 130.1 110.7 122 116.4 116.3C122.1 110.6 130.2 108.2 138 109.7L241.3 129.9L300.1 42.5L301.9 40.2C306.4 35 313 32 320 32zM272.2 170C266.8 178 257.2 182 247.7 180.2L163.7 163.8L180.1 247.8C181.9 257.3 177.9 266.9 169.9 272.3L99 320L170 367.8C178 373.2 182 382.8 180.2 392.3L163.8 476.3L247.8 459.9L251.3 459.5C259.6 459.1 267.6 463.1 272.3 470.1L320.1 541.1L367.9 470.1L370.1 467.3C375.7 461.2 384.1 458.3 392.4 460L476.4 476.4L460 392.4C458.2 382.9 462.2 373.3 470.2 367.9L541.2 320.1L470.2 272.3C462.2 266.9 458.2 257.3 460 247.8L476.4 163.8L392.4 180.2C382.9 182 373.3 178 367.9 170L320.1 99L272.3 170zM320 440C253.7 440 200 386.3 200 320C200 253.7 253.7 200 320 200C386.3 200 440 253.7 440 320C440 386.3 386.3 440 320 440zM320 248C280.2 248 248 280.2 248 320C248 359.8 280.2 392 320 392C359.8 392 392 359.8 392 320C392 280.2 359.8 248 320 248z" />
						</svg>
					</div>
					<span>
						{text.tip}
					</span>
				</div>
			</div>
		</div>
	);
};

export default CameraScreen;

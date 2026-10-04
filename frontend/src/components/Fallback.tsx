// import { useContext } from "react";
// import DataContext from "../context/DataContext";

// type FallbackProviderProps = {
// 	message: string;
// 	mode: string;
// };

// const Fallback = ({ message, mode }: FallbackProviderProps) => {
// 	const ctx = useContext(DataContext);
// 	let text;
// 	if (mode == "default") {
// 		if (ctx?.language == "English") {
// 			text = message;
// 		} else {
// 			text =
// 				"Labari mai dadi — wannan amfanin gona yana da kyau sosai! Ba ya bukatar wani magani.";
// 		}
// 	} else if (mode == "unconfident") {
// 		if (ctx?.language == "English") {
// 			text = message;
// 		} else {
// 			text =
// 				"Ba mu da cikakken tabbaci game da wannan sakamakon. Da fatan za a sake gwada duba shi ta hanyar amfani da hoto mai kyau da kuma bayyananniya.";
// 		}
// 	} else {
// 		if (ctx?.language == "English") {
// 			text = message;
// 		} else {
// 			text = "Babu sakamako. Da fatan za a sake gwadawa.";
// 		}
// 	}
// 	return (
// 		<div className="w-full h-30 flex justify-center items-center md:w-fit mt-10 md:mt-0">
// 			<div className=" h-fit flex flex-col gap-.5  p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full md:w-fit">
// 				<span className="text-[#0F6E56] text-md font-bold">{text}</span>
// 			</div>
// 		</div>
// 	);
// };

// export default Fallback;

import { useContext } from "react";
import DataContext from "../context/DataContext";

type FallbackMode = "healthy" | "unconfident" | "unrecognized";

type FallbackProviderProps = {
	message: string;
	mode: FallbackMode;
};

const HAUSA_TEXT: Record<FallbackMode, string> = {
	healthy:
		"Labari mai daɗi — wannan amfanin gonarku yana da lafiya sosai! Ba ya buƙatar wani magani.",
	unconfident:
		"Ba mu da cikakken tabbaci game da wannan sakamakon. Da fatan za a sake ɗaukar hoto mai bayyana sosai kuma a sake gwadawa.",
	unrecognized:
		"Ba a gane wata cuta a cikin wannan hoton ba. Da fatan za a tabbatar hoton ya nuna ganyen shukar a fili, yana da kyakkyawan haske, kuma ya cika yawancin firam ɗin, sannan a sake gwadawa.",
};

const IGBO_TEXT: Record<FallbackMode, string> = {
	healthy: "Ozi ọma — osisi a dị mma! Ọ dịghị mkpa ọgwụgwọ.",
	unconfident: "Anyị ejighị n'aka nke ọma banyere nsonaazụ a. Biko see foto doro anya karị ma nwaa ọzọ.",
	unrecognized: "Anyị achọpụtaghị ọrịa osisi na foto a. Biko hụ na foto ahụ gosiri akwụkwọ osisi nke ọma, dị nkọ ma nwee ezigbo ìhè, wee nwaa ọzọ.",
};

const YORUBA_TEXT: Record<FallbackMode, string> = {
	healthy: "Ìròyìn ayọ̀ — irúgbìn yìí ní ìlera! Kò nílò ìtọ́jú kankan.",
	unconfident: "A kò dá wa lójú tó nípa àbájáde yìí. Jọ̀wọ́ ya fọ́tò tó ṣe kedere sí i, kí o sì tún gbìyànjú.",
	unrecognized: "A kò rí àrùn irúgbìn kankan nínú fọ́tò yìí. Jọ̀wọ́ rí i dájú pé ewé hàn kedere, fọ́tò náà sì mọ́lẹ̀ dáadáa, kí o sì tún gbìyànjú.",
};

const Fallback = ({ message, mode }: FallbackProviderProps) => {
	const ctx = useContext(DataContext);
	const text =
		ctx?.language === "Hausa"
			? HAUSA_TEXT[mode]
			: ctx?.language === "Igbo"
				? IGBO_TEXT[mode]
				: ctx?.language === "Yoruba"
					? YORUBA_TEXT[mode]
					: message;

	return (
		<div
			className={`w-full h-30 flex justify-center items-center md:w-fit mt-10 md:mt-0 ${mode != "healthy" ? "lg:col-span-2" : ""}`}
		>
			<div className="h-fit flex flex-col gap-.5 p-3 px-4 rounded-lg border-2 border-[#A8D0C5] bg-[#F7FAF9] w-full md:w-fit">
				<span className="text-[#0F6E56] text-md font-bold">{text}</span>
			</div>
		</div>
	);
};

export default Fallback;

import { useContext } from "react";
import LoadingAnimation from "../components/LoadingAnimation";
import DataContext from "../context/DataContext";

const LoadingScreen = () => {
	const ctx = useContext(DataContext);
	return (
		<div className="w-screen h-screen bg-[#1f1e1e81] flex justify-center items-center fixed top-0 left-0 overflow-hidden z-50">
			<article className="bg-white p-5 rounded-xl flex flex-col gap-4 items-center justify-center border-2 border-[#E8F5F1] ">
				<LoadingAnimation />
				<span className="text-sm font-semibold">
					{ctx?.language === "Hausa"
						? "Ana nazarin hotonka..."
						: ctx?.language === "Igbo"
							? "A na-enyocha foto gị..."
							: ctx?.language === "Yoruba"
								? "A ń ṣe àyẹ̀wò fọ́tò rẹ..."
								: "Analyzing your photo..."}
				</span>
			</article>
		</div>
	);
};

export default LoadingScreen;

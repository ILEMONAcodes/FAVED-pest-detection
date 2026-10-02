import { useContext } from "react";
import DataContext from "../context/DataContext";

type BadgeProviderProps = {
	status: "healthy" | "diseased";
};

const Badge = ({ status }: BadgeProviderProps) => {
	const ctx = useContext(DataContext);
	const labels = {
		English: { diseased: "diseased", healthy: "healthy" },
		Hausa: { diseased: "mai cuta", healthy: "mai lafiya" },
		Igbo: { diseased: "nwere ọrịa", healthy: "dị mma" },
		Yoruba: { diseased: "ní àrùn", healthy: "ní ìlera" },
	};
	const statusByLang = labels[ctx?.language ?? "English"][status];

	return (
		<article
			className={` px-2 pr-3 rounded-4xl flex gap-1.5 items-center ${status === "healthy" ? "bg-[#A8D0C5] text-[#0F6E56]" : "bg-[#FFCCCB] text-[#FF7f7f]"}`}
		>
			<div
				className={`w-2 h-2 rounded-full my-2.5 ${status === "healthy" ? "bg-[#0F6E56]" : "bg-[#FF7F7F]"}`}
			></div>
			<span className="text-md font-medium capitalize">
				{statusByLang}
			</span>
		</article>
	);
};

export default Badge;

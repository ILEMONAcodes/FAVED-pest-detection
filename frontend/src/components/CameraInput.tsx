import { useContext, useState } from "react";
import DataContext from "../context/DataContext";

type CameraInputPropsProvider = {
	clickFunction: () => void;
};

const CameraInput = ({ clickFunction }: CameraInputPropsProvider) => {
	const ctx = useContext(DataContext);
	const [isDragging, setIsDragging] = useState<boolean>(false);

	return (
		<div
			className="w-full  lg:col-span-1 lg:row-span-2 "
			onDragOver={(e) => {
				e.preventDefault();
				setIsDragging(true);
			}}
			onDragLeave={() => {
				setIsDragging(false);
			}}
			onDrop={(e) => {
				e.preventDefault();
				setIsDragging(false);
				ctx?.uploadImage(e.dataTransfer.files);
			}}
		>
			{!ctx?.imageLoaded ? (
				<div
					className={`group p-6 flex flex-col justify-center  items-center gap-6 rounded-2xl border-4 border-dashed  hover:bg-[#E8F5F1] cursor-pointer hover:border-[#0F6E56] transition-all ${isDragging ? "bg-[#E8F5F1] border-[#0F6E56]" : "border-[#A8D0C5] bg-[#F7FAF9]"} aspect-4/3 md:aspect-3/2`}
					onClick={clickFunction}
				>
					<div className="p-4 rounded-lg bg-[#E8F5F1] w-fit group-hover:bg-[#D4EDE7] transition-all">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 640 640"
							className="w-10 h-10 fill-[#0F6E56]"
						>
							<path d="M257.1 96C238.4 96 220.9 105.4 210.5 120.9L184.5 160L128 160C92.7 160 64 188.7 64 224L64 480C64 515.3 92.7 544 128 544L512 544C547.3 544 576 515.3 576 480L576 224C576 188.7 547.3 160 512 160L455.5 160L429.5 120.9C419.1 105.4 401.6 96 382.9 96L257.1 96zM250.4 147.6C251.9 145.4 254.4 144 257.1 144L382.8 144C385.5 144 388 145.3 389.5 147.6L422.7 197.4C427.2 204.1 434.6 208.1 442.7 208.1L512 208.1C520.8 208.1 528 215.3 528 224.1L528 480.1C528 488.9 520.8 496.1 512 496.1L128 496C119.2 496 112 488.8 112 480L112 224C112 215.2 119.2 208 128 208L197.3 208C205.3 208 212.8 204 217.3 197.3L250.5 147.5zM320 448C381.9 448 432 397.9 432 336C432 274.1 381.9 224 320 224C258.1 224 208 274.1 208 336C208 397.9 258.1 448 320 448zM256 336C256 300.7 284.7 272 320 272C355.3 272 384 300.7 384 336C384 371.3 355.3 400 320 400C284.7 400 256 371.3 256 336z" />
						</svg>
					</div>
					<article className="flex flex-col gap md:text-sm items-center text-center text-[.8rem]">
						<span>
							{ctx?.language === "Hausa"
								? "Danna don ɗaukar hoton shukarka"
								: ctx?.language === "Igbo"
									? "Pịa ka see foto osisi gị"
									: ctx?.language === "Yoruba"
										? "Fọwọ́ kan láti ya fọ́tò ohun ọ̀gbìn rẹ"
										: "Tap to take a photo of your plant"}
						</span>
						<span>
							{ctx?.language === "Hausa"
								? "ko kuma ka ja ka ajiye hoto"
								: ctx?.language === "Igbo"
									? "ma ọ bụ dọrọ ma tụba foto"
									: ctx?.language === "Yoruba"
										? "tàbí fa fọ́tò wá síbí"
										: "or drag and drop an image"}
						</span>
					</article>
				</div>
			) : (
				<div
					className={`rounded-2xl overflow-hidden border-3 aspect-4/3 object-cover md:aspect-3/2 ${isDragging ? " border-[#0F6E56]" : "border-[#A8D0C5] "}`}
				>
					<img src={ctx?.imgUrl} alt="" className="w-full h-full" />
				</div>
			)}
		</div>
	);
};

export default CameraInput;

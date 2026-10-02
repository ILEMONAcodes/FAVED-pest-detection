type RecommendedProviderProps = {
	step: string;
	id: number;
};

const RecommendedStep = ({ id, step }: RecommendedProviderProps) => {
	return (
		<div className="flex w-full gap-4 py-2.5 px-4 border-b border-[#A8D0C5] nth-last-[1]:border-b-0">
			<span className="w-8 h-8 rounded-full p-4 font-bold text-[#0F6E56] bg-[#A8D0C5] flex justify-center items-center">
				{String(id).padStart(2, "0")}
			</span>
			<p className="font-normal">{step}</p>
		</div>
	);
};

export default RecommendedStep;

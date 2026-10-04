type ButtonPropsProvider = {
	text: string;
	clickFunction: () => void;
	type: string;
};

const Button = ({ text, clickFunction, type }: ButtonPropsProvider) => {
	const ClickHandler = () => {
		clickFunction();
	};

	return (
		<button
			onClick={ClickHandler}
			className={`w-full rounded-xl flex justify-center items-center  font-semibold py-2 px-4 shadow cursor-pointer ${type === "main" ? "bg-[#0F6E56]" : "border-3 border-[#A8D0C5]"} ${type !== "main" ? "text-[#0F6E56]" : "text-white"} `}
		>
			{text}
		</button>
	);
};

export default Button;

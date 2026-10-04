import { useContext, useState, useEffect } from "react";
import DataContext from "../context/DataContext";

const Header = () => {
	const [menuOpen, setMenuOpen] = useState(false);
	const ctx = useContext(DataContext);

	useEffect(() => {
		if (menuOpen) {
			document.body.classList.add("overflow-hidden");
		} else {
			document.body.classList.remove("overflow-hidden");
		}

		return () => {};
	}, [menuOpen]);

	return (
		<header className="w-full flex justify-between items-center p-2 fixed top-0 left-0 md:relative bg-white ">
			<article className="flex gap-2 p-2 items-center justify-center">
				<div className="p-2 rounded-md bg-green-900">
					<svg
						width="24"
						height="24"
						fill="#NaNNaNNaN"
						viewBox="0 0 24 24"
						transform=""
						id="injected-svg"
						xmlns="http://www.w3.org/2000/svg"
						className="fill-white w-4 h-4"
					>
						<path d="M21.33 2.53c-.37-.14-.79-.05-1.07.22-.08.07-1.86 1.77-4.85.27-2.05-1.03-5.6-1.64-8.88 0C2.24 5.18.73 10.61 3.1 15.37c.38.76.83 1.42 1.34 2.01-.29 1.4-.45 2.94-.45 4.62h2c0-1.15.07-2.18.21-3.12.67.41 1.39.72 2.17.9.66.16 1.32.22 1.97.22 2.43 0 4.64-.96 5.72-1.77 1.82-1.37 3.32-2.67 4.8-5.89 1.4-3.07 1.12-8.7 1.1-8.94a.99.99 0 0 0-.64-.87Zm-2.28 8.98c-1.29 2.81-2.49 3.85-4.18 5.13-1.1.83-3.7 1.75-6.03 1.2-.82-.19-1.55-.56-2.19-1.08 1.85-6.59 7.09-6.73 7.35-6.73v-2c-.17 0-3.49.04-6.29 2.83-1.11 1.1-1.95 2.48-2.57 4.1-.09-.15-.17-.3-.25-.46-1.65-3.3-1.14-7.82 2.54-9.68 1.16-.58 2.37-.81 3.49-.81 1.4 0 2.68.35 3.59.81 2.36 1.18 4.24.92 5.48.42-.02 1.8-.18 4.6-.95 6.29Z"></path>
					</svg>
				</div>
				<h1 className="font-bold">FAVE</h1>
			</article>

			<div
				className="menu-btn w-10 h-10 p-2 rounded-full cursor-pointer hover:bg-[#e4e4e4c5] justify-self-end md:hidden"
				onClick={() => {
					setMenuOpen(true);
				}}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 640 640"
					className="fill-black"
				>
					<path d="M96 160C96 142.3 110.3 128 128 128L512 128C529.7 128 544 142.3 544 160C544 177.7 529.7 192 512 192L128 192C110.3 192 96 177.7 96 160zM96 320C96 302.3 110.3 288 128 288L512 288C529.7 288 544 302.3 544 320C544 337.7 529.7 352 512 352L128 352C110.3 352 96 337.7 96 320zM544 480C544 497.7 529.7 512 512 512L128 512C110.3 512 96 497.7 96 480C96 462.3 110.3 448 128 448L512 448C529.7 448 544 462.3 544 480z" />
				</svg>
			</div>

			<div
				className={`menu-bar fixed top-0 left-0 h-screen z-50 w-full ${menuOpen ? "block" : "hidden md:block"} md:absolute md:top-[calc(100%)] md:h-[calc(100vh-60px)] md:w-fit`}
			>
				<div
					className="bg-[#00000086] w-screen h-screen md:hidden"
					onClick={() => {
						setMenuOpen(false);
					}}
				></div>

				<div className="w-60 md:w-40 lg:w-60 bg-white h-full fixed top-0 left-0 flex flex-col md:relative  md:h-[calc(100vh-60px)] overflow-hidden md:justify-end">
					<span className="w-full p-3 bg-[#056e56] text-white font-bold">
						{ctx?.language === "Igbo"
							? "Asụsụ:"
							: ctx?.language === "Yoruba"
								? "Èdè:"
								: ctx?.language === "Hausa"
									? "Harshe:"
									: "Language:"}
					</span>
					<ul className="flex flex-col w-full font-bold">
						<li
							className={`w-full p-2 md:px-4 hover:bg-[#e4e4e4c5] cursor-pointer pl-6 transition-colors ${ctx?.language == "English" ? "text-[#056e56] font-extrabold" : ""}`}
							onClick={() => {
								ctx?.setLanguage("English");
							}}
						>
							English
						</li>
						<li
							className={`w-full p-2 md:px-4 hover:bg-[#e4e4e4c5] cursor-pointer pl-6 transition-colors ${ctx?.language == "Hausa" ? "text-[#056e56] font-extrabold" : ""}`}
							onClick={() => {
								ctx?.setLanguage("Hausa");
							}}
						>
							Hausa
						</li>
						<li
							className={`w-full p-2 md:px-4 hover:bg-[#e4e4e4c5] cursor-pointer pl-6 transition-colors ${ctx?.language == "Igbo" ? "text-[#056e56] font-extrabold" : ""}`}
							onClick={() => {
								ctx?.setLanguage("Igbo");
							}}
						>
							Igbo
						</li>
						<li
							className={`w-full p-2 md:px-4 hover:bg-[#e4e4e4c5] cursor-pointer pl-6 transition-colors ${ctx?.language == "Yoruba" ? "text-[#056e56] font-extrabold" : ""}`}
							onClick={() => {
								ctx?.setLanguage("Yoruba");
							}}
						>
							Yorùbá
						</li>
					</ul>
				</div>
			</div>
		</header>
	);
};

export default Header;

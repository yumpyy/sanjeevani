import Image from "next/image";
import Bg_video from "@/components/background-vid";
import Logo from "@/components/logo";
import MiscContainer from "@/components/MiscContainer";
import Login from "@/components/Login";
import MainText1 from "@/components/MainText1";
import MainText2 from "@/components/MainText2";
import GetStarted from "@/components/GetStarted";
import "./mainContainer.css";

export default function Home() {
  return (
    <div id="mainContainer">
      <Bg_video/>
      <Logo/>
      <MiscContainer></MiscContainer>
      <Login></Login>
      <MainText1/>
      <MainText2/>
      <GetStarted/>
    </div>
  );
}

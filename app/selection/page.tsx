import Bg_video from "@/components/background-vid";
import MiscContainer from "@/components/MiscContainer";
import Login from "@/components/Login";
import MainText1 from "@/components/MainText1";
import MainText2 from "@/components/MainText2";
import GetStarted from "@/components/GetStarted";
import DocContainer from "@/components/DocContainer";
import Logoselect from "@/components/logo(select)";
import "../../components/componentStyles/mainContainer2.css";

export default function Home() {
  return (
    <div id="mainContainer2">
      <Bg_video/>
      <Logoselect/>
      <MiscContainer></MiscContainer>
      <Login></Login>
      <MainText1/>
      <MainText2/>
      <GetStarted/>
      <DocContainer/>
    </div>
  );
}
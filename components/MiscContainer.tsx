import AboutUs from "./AboutUs";
import MoreLinks from "./MoreLinks";
import ContactUs from "./ContactUs";
import "./componentStyles/miscContainer.css"

function MiscContainer(){
    return(
        <div id="miscContainer">
            <AboutUs/>
            <ContactUs/>
            <MoreLinks/>
        </div>
    )
}
export default MiscContainer;
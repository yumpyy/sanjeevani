import "./componentStyles/docPicContainer.css";

function Docpicture({source}){
    return(
        <div id="docPicContainer">
            <img src={source}></img>
        </div>
    )
}
export default Docpicture;
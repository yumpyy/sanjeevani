"use client"
import { useState } from "react";
import "./componentStyles/specialist.css";
import Docpicture from "./Docpicture";

function Specialist(){
    let [srcString,setsrcString]=useState("/oldwoman.jpg");
    function oldwoman(){
        setsrcString("/oldwoman.jpg");
    }
    function dermatologist(){
        setsrcString("/oldman.jpg");
    }
    function therapist(){
        setsrcString("/youngman.jpg");
    }
    function ent(){
        setsrcString("/youngwoman.jpg");
    }
    return(
        <div id="specialistContainer">
            <Docpicture source={srcString}/>
            <button className="button" id="general" onClick={ent}>
                <div>E.N.T Specialist</div>
            </button>
            <button className="button" id="therapist" onClick={dermatologist}>
                <div>Dermatologist</div>
            </button>
            <button className="button" id="dermatologist" onClick={therapist}>
                <div>Therapist</div>
            </button>
            <button className="button" id="ent" onClick={oldwoman}>
                <div>General Practicioner</div>
            </button>
            <div id="choose">Choose your doctor</div>
        </div>
    )
}
export default Specialist;
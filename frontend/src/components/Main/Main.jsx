import React, { useState } from 'react';
import './Main.css';
import { assets } from '../../assets/assets';

const Main = () => {

    const [buttonJiraIsActive, buttonJirasetActive] = useState(false);
    const [buttonUMLIsActive, buttonUMLsetActive] = useState(false);
    const [buttonReactIsActive, buttonReactsetActive] = useState(false);


    return (
        <div className="main">
            <div className="nav">
                <p>InfyCode</p>
                <img src={assets.user_icon} alt='user icon'/>
            </div>
            <div className="main-container">
                <div className="greet">
                    <p>
                        <span>Hello, Julieta.</span>
                    </p>
                    <p>
                        <span>What are we developing today?</span>
                    </p>
                </div>
                <div className="cards">
                    <div className="card">
                        <p>Documents</p>
                        <div>
                        <button className={buttonJiraIsActive ? 'active': null} onClick={()=>buttonJirasetActive(prev=>!prev)} >Jira Stories</button>
                        </div>
                        <img src={assets.compass_icon}/>
                    </div>
                    <div className="card">
                        <p>Diagrams</p>
                        <div>
                        <button className={buttonUMLIsActive ? 'active': null} onClick={()=>buttonUMLsetActive(prev=>!prev)} >UML</button>
                        </div>
                        <img src={assets.bulb_icon}/>
                    </div>
                    <div className="card">
                        <p>Code</p>
                        <div>
                        <button className={buttonReactIsActive ? 'active': null} onClick={()=>buttonReactsetActive(prev=>!prev)} >React</button>
                        </div>
                        <img src={assets.code_icon}/>
                    </div>
                </div>
                <div className="main-bottom">
                    <div className="search-box">
                        <input type='text' placeholder='input your project requirements...'/>
                        <div>
                            <img src={assets.gallery_icon} alt="" />
                            <img src={assets.mic_icon} alt="" />
                            <img src={assets.send_icon} alt="" />
                        </div>
                    </div>
                    <p className='bottom-info'>
                        specify the outputs you require bellow!
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Main;
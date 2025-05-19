import React, { useState } from 'react';
import './Main.css';
import { assets } from '../../assets/assets';

const Main = () => {

    const [buttonGraphvizIsActive, buttonGraphvizsetActive] = useState(false);
    const [buttonMermaidIsActive, buttonMermaidsetActive] = useState(false);
    const [buttonUMLIsActive, buttonUMLsetActive] = useState(false);
    const [buttonPythonIsActive, buttonPythonsetActive] = useState(false);
    const [buttonJavaScriptIsActive, buttonJavaScriptsetActive] = useState(false);
    const [buttonJavaIsActive, buttonJavasetActive] = useState(false);
    const [buttonCppIsActive, buttonCppsetActive] = useState(false);
    const [buttonCsharpIsActive, buttonCsharpsetActive] = useState(false);
    const [buttonPHPIsActive, buttonPHPsetActive] = useState(false);
    const [buttonRubyIsActive, buttonRubysetActive] = useState(false);
    const [buttonGoIsActive, buttonGosetActive] = useState(false);
    const [buttonSwiftIsActive, buttonSwiftsetActive] = useState(false);
    const [buttonKotlinIsActive, buttonKotlinsetActive] = useState(false);
    const [buttonSQLIsActive, buttonSQLsetActive] = useState(false);
    const [buttonHTMLIsActive, buttonHTMLsetActive] = useState(false);
    const [buttonCSSIsActive, buttonCSSsetActive] = useState(false);
    const [inputValue, setInputValue] = useState("");


    return (
        <div className="main">
            <div className="nav">
                <p>InfyCode</p>
                <img src={assets.user_icon} alt='user icon'/>
            </div>
            <div className="main-container">
                <div className="greet">
                    <p>
                        <span>Hello!</span>
                    </p>
                    <p>
                        <span>What are we developing today?</span>
                    </p>
                </div>
                <div className="cards">
                    <div className="card">
                        <p>Diagrams</p>
                        <div>
                        <button className={buttonUMLIsActive ? 'active': null} onClick={()=>buttonUMLsetActive(prev=>!prev)} >UML</button>
                        <button className={buttonGraphvizIsActive ? 'active': null} onClick={()=>buttonGraphvizsetActive(prev=>!prev)} >Graphviz</button>
                        <button className={buttonMermaidIsActive ? 'active': null} onClick={()=>buttonMermaidsetActive(prev=>!prev)} >Mermaid</button>
                        </div>
                        <img src={assets.bulb_icon}/>
                    </div>
                    <div className="card">
                        <p>Code</p>
                        <div>
                        <button className={buttonPythonIsActive ? 'active': null} onClick={()=>buttonPythonsetActive(prev=>!prev)} >Python</button>
                        <button className={buttonJavaScriptIsActive ? 'active': null} onClick={()=>buttonJavaScriptsetActive(prev=>!prev)} >JavaScript</button>
                        <button className={buttonJavaIsActive ? 'active': null} onClick={()=>buttonJavasetActive(prev=>!prev)} >Java</button>
                        <button className={buttonCppIsActive ? 'active': null} onClick={()=>buttonCppsetActive(prev=>!prev)} >C++</button>
                        <button className={buttonCsharpIsActive ? 'active': null} onClick={()=>buttonCsharpsetActive(prev=>!prev)} >C#</button>
                        <button className={buttonPHPIsActive ? 'active': null} onClick={()=>buttonPHPsetActive(prev=>!prev)} >PHP</button>
                        <button className={buttonRubyIsActive ? 'active': null} onClick={()=>buttonRubysetActive(prev=>!prev)} >Ruby</button>
                        <button className={buttonGoIsActive ? 'active': null} onClick={()=>buttonGosetActive(prev=>!prev)} >Go</button>
                        <button className={buttonSwiftIsActive ? 'active': null} onClick={()=>buttonSwiftsetActive(prev=>!prev)} >Swift</button>
                        <button className={buttonKotlinIsActive ? 'active': null} onClick={()=>buttonKotlinsetActive(prev=>!prev)} >Kotlin</button>
                        <button className={buttonSQLIsActive ? 'active': null} onClick={()=>buttonSQLsetActive(prev=>!prev)} >SQL</button>
                        <button className={buttonHTMLIsActive ? 'active': null} onClick={()=>buttonHTMLsetActive(prev=>!prev)} >HTML</button>
                        <button className={buttonCSSIsActive ? 'active': null} onClick={()=>buttonCSSsetActive(prev=>!prev)} >CSS</button>
                        </div>
                        <img src={assets.code_icon}/>
                    </div>
                </div>
                <div className="main-bottom">
                    <div className="search-box">
                        <input type='text' placeholder='Input your project requirements here...' value={inputValue} onChange={e => setInputValue(e.target.value)}/>
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
const fs = require('fs');

// Read the recovered Javascript file
let content = fs.readFileSync('recovered_app_js_step58.js', 'utf8');

// We want to extract the state variable. Let's make sure it is exported.
// We can append code to export the state variable.
content = content + "\n\nmodule.exports = state;";

// Write to a temporary file
fs.writeFileSync('temp_app_state.js', content, 'utf8');

try {
    const tempState = require('./temp_app_state.js');
    const data = tempState.data;
    
    // Save to a clean JSON file
    fs.writeFileSync('original_mock_data.json', JSON.stringify(data, null, 4), 'utf8');
    console.log(`SUCCESS: Extracted original mock data! Found ${data.bicicletas.length} bicycles and ${data.repuestos.length} repuestos.`);
} catch (e) {
    console.error("Failed to require temp_app_state.js directly. Trying eval...", e);
    try {
        // Fallback to simple regex/eval if require fails
        const evalContent = content.replace('module.exports = state;', '') + "\nstate;";
        const stateObj = eval(evalContent);
        fs.writeFileSync('original_mock_data.json', JSON.stringify(stateObj.data, null, 4), 'utf8');
        console.log(`SUCCESS: Extracted via eval! Found ${stateObj.data.bicicletas.length} bicycles.`);
    } catch (evalErr) {
        console.error("Eval failed too:", evalErr);
    }
}

// Clean up
try {
    fs.unlinkSync('temp_app_state.js');
} catch (err) {}

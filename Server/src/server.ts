import express, {Express, Request, Response} from 'express';
import Device from './model/core/device/Device';
import bodyParser from 'body-parser';

// Setup server
const app: Express = express();
const port = 8080;

app.listen(port, () => {
    console.log(`[Server]: I am running at http://localhost:${port}`);
});

let DEVICES: Device[] = [];
let BLOCK_COMMANDS = false;
let emergencyState = false;

DEVICES.push(new Device("1"));
DEVICES.push(new Device("2"));
DEVICES.push(new Device("3"));
DEVICES.push(new Device("4"));
DEVICES.push(new Device("5"));
DEVICES.push(new Device("6"));

app.get('/', (req: Request, res: Response) => {
    res.send('LUCI-REALITY');
});

// get kill commands
app.get('/blockCommands', (_, res) => {
    res.send(JSON.stringify({
        BLOCK_COMMANDS: BLOCK_COMMANDS
    }));
});

// get devices
app.get('/devices', (req, res) => {
    res.send(JSON.stringify({
        devices: DEVICES
    }));
});

// get device
app.get('/device/:deviceId', (req, res) => {
    const id = req.params.deviceId;
    const device = DEVICES.find(device => device.id == id);

    if (device == undefined){
        console.error(`Could not get device with ID ${id}`);
    }

    res.send(JSON.stringify({
        device: device
    }));
});

// add a new endpoint to handle updates from Emergency Button Device regarding emergency state
app.post('/updateEmergencyState/:deviceId', bodyParser.json(), (req, res) => {
    const deviceId = req.params.deviceId;
    const newEmergencyState = req.body.emergencyState;

    // Update the global emergency state variable
    emergencyState = newEmergencyState;

    console.log(`Received emergency state update from device ${deviceId}: ${emergencyState}`);
    
    res.status(200).send({ message: "Emergency state updated" });
});

// Add a new endpoint to get the global emergency state
app.get('/emergencyState', (_, res) => {
    res.send(JSON.stringify({
        emergencyState: emergencyState
    }));
});

// get commands for device
app.get('/commands/:deviceId', (req, res) => {
    const id = req.params.deviceId;
    const device = BLOCK_COMMANDS ? undefined : DEVICES.find(device => device.id == id);

    if (device == undefined){
        console.error(`Could not get device with ID ${id}`);
    }

    res.send(JSON.stringify({
        commands: device?.commands || []
    }));
});

// get next command
app.get('/command/:deviceId', (req, res) => {
    const id = req.params.deviceId;
    const device = DEVICES.find(device => device.id == id);

    const command = device?.getNextCommand();

    if (device == undefined){
        console.error(`Could not get device with ID ${id}`);
    }else if (command == undefined || BLOCK_COMMANDS){
        console.error(`Could not get next command`);
    }

    res.send(JSON.stringify({
        command: !BLOCK_COMMANDS ? command : undefined
    }));
})

// blocks commands, and clears all current commands
app.post('/blockCommands', bodyParser.json(), (req, res) => {
    DEVICES.map(device => {
         device.clearCommands();
         return device;
    })
    BLOCK_COMMANDS = true;
    res.status(200).send({ message: "Commands blocked" });
})

app.post('/unblockCommands', bodyParser.json(), (req, res) => {
    BLOCK_COMMANDS = false;
    res.status(200).send({ message: "Commands unblocked" });
})

// add device
app.post('/device/:deviceId', bodyParser.json(), (req, res) => {
    let id = req.params.deviceId

    DEVICES.push(new Device(id));
    res.status(200).send({ message: 'Device added' });
})

// add command
app.post('/command/:deviceId/:commandName', bodyParser.json(), (req, res) => {

    const payload = req.body

    let id = req.params.deviceId
    let commandName = req.params.commandName

    const device = DEVICES.find(device => device.id == id);
    if (device == undefined){
        console.error(`Could not get device with ID ${id}`);
        res.status(400).send({ error: 'Device does not exist' });
    }
    
    const success = device?.addCommand(commandName, payload);
    if (!success){
        console.error(`Invalid command name`);
    }

    if (success){
        DEVICES = DEVICES.map(d => d.id == device?.id ? device : d);
        res.status(200).send({ message: 'Command added' });
        console.log("Command received for: Device " + device?.id)
    }
})

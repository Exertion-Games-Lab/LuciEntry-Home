# Table of Contents

1. [Overview](#overview)

2. [System Architecture](#system-architecture)

  1. [Server Model](#server-model)

    1. [Instruction](#instruction)

    2. [Command](#command)

    3. [Device](#device)

  2. [Endpoints](#endpoints)

    1. GET /
       
    2. GET /blockCommands
       
    3. GET /devices
       
    4. GET /device/:deviceId
       
    5. GET /commands/:deviceId
       
    6. GET /command/:deviceId
       
    7. POST /blockCommands
       
    8. POST /unblockCommands
       
    9. POST /device/:deviceId
       
    10. POST /command/:deviceId/:commandName

  3. [Onboarding](#onboarding)

    1. [Instructions](#instructions)

    2. [Commands](#commands)

3. [New Pi Setup Procedure](#new-pi-setup-procedure)

  1. [Setting up your new Raspberry Pi](#setting-up-your-new-raspberry-pi)

  2. [Downloading Dependencies](#installing-dependencies)

  3. [Cloning Server Codes](#cloning-server-codes)

# Overview
This README markdown file contains the system architecture for the server that controls the LuciEntry HOME prototype, developed by Exertion Games Lab for Lucid Dreaming research.

# System Architecture

## Server Model

### Instruction

An Instruction is a base class representing a singular action or operation that a device should perform. It is abstract and should be extended to create new, specific instructions for commands. It has a `code` representing the type of the instruction and a `payload` containing the data needed for the instruction execution.

To create a new Instruction, extend the Instruction class and define the specific behaviour and properties you require. Here’s a basic outline:

```ts
interface NewPayloadType {
    // data
}

class NewInstruction extends Instruction<NewPayloadType> {
    constructor(payload: NewPayloadType) {
        super(InstructionCode.NewInstructionCode, payload);
    }
}
```

`InstructionCode` is an enumeration defining the different possible instruction types. When creating a new instruction, you should add a new code to this enumeration to represent your new instruction type.

### Command

A Command is an abstract class representing a grouped set of Instructions. It allows a batch of Instructions to be sent together to a device. Each Command has a unique `id`, a `name` representing the type of command, an array of `instructions`, and the number of instructions `noOfInstructions`.

If a payload is provided when adding a command, it will be passed to the command, necessitating every command to implement a `setPayload` method to handle the incoming payload.

`CommandName` is an enumeration that defines different possible command types. When creating a new command, add a new name to this enumeration to represent your new command type.
### Device

A Device is a class representing a unique entity capable of receiving and executing Commands. It holds information like `id` and the list of `commands` it should execute.

```ts
public addCommand(command: string | Command, payload?: any): boolean {

    const newCommand: Command | undefined = (typeof command == "string") ? CommandMap.get(command)?.clone() : command;
	
    newCommand?.setPayload(payload || {});
	
    if (newCommand == undefined){
        console.error(`Could not find command`);
	return false
    }
	
    this._commands.push(newCommand);
	
    return true;

}
```

The payload can be any type, this is because it will be passed in the body of the request, therefore, there is no way we can know the type. To ensure the server does not crash you should handle invalid payloads in the `setPayload` method.

In the future, the expectation is to have devices connect themselves to the server when they are turned on. This would likely involve some form of automatic device registration and handshake process between the device and the server to establish a connection and exchange necessary information, such as the device's ID and capabilities.
## Endpoints

markdownCopy code

#### `GET /` 
- **Description:** Serves the root of the server. 
- **Response:** `LUCI-REALITY`  
#### `GET /blockCommands` 
- **Description:** Retrieves the block status of commands. 
- **Response:**
```json 
{     
    "BLOCK_COMMANDS": boolean
}
```

#### `GET /devices`

- **Description:** Retrieves a list of all connected devices.
- **Response:**
```json
{   
    "devices": Device[]
}
```

#### `GET /device/:deviceId`

- **Description:** Retrieves information of a specific device by ID.
- **Parameters:** `deviceId` - ID of the device.
- **Response:**
```json
{
  "device": Device
}
```

#### `GET /commands/:deviceId`

- **Description:** Retrieves all commands for a specific device by ID. Commands are blocked if `BLOCK_COMMANDS` is true.
- **Parameters:** `deviceId` - ID of the device.
- **Response:**   
```json
{
  "commands": Command[]
}
```
#### `GET /command/:deviceId`

- **Description:** Retrieves the next command for a specific device by ID.
- **Parameters:** `deviceId` - ID of the device.
- **Response:**
```json
{
  "command": Command
}
```
#### `POST /blockCommands`

- **Description:** Blocks all commands and clears the current commands for all devices.
- **Response:**
```json
{
  "message": "Commands blocked"
}
```
#### `POST /unblockCommands`

- **Description:** Unblocks all the commands.
- **Response:**
```json
{
  "message": "Commands unblocked"
}
```
#### `POST /device/:deviceId`

- **Description:** Adds a new device.
- **Parameters:** `deviceId` - ID of the new device.
- **Response:**
```json
{
  "message": "Device added"
}
```
#### `POST /command/:deviceId/:commandName`

- **Description:** Adds a new command to a specific device by ID.
- **Parameters:**
    - `deviceId` - ID of the device.
    - `commandName` - Name of the command.
- **Request Body:** Payload for the command.
- **Response:**
```json
{
  "message": "Command added"
}
```

## Onboarding
This md is for onboarding devs.

### Instructions

Add the instruction code to the `InstructionCode` enum.

```typescript
export enum InstructionCode {
	NEW_INSTRUCTION = unique_code
}
```

Create a new `Instruction`

```typescript
interface Payload {
  // Put whatever object attributes you need for the payload
}

class NewInstruction extends Instruction<Payload> {
  
  public constructor(payload_props){
    super(InstructionCode.NEW_INSTRUCTION, payload)
  }
  
}
```

### Commands

Add the name to the `CommandName` enum

```typescript
export enum CommandName {
    NEW_COMMAND = "NewCommand"
}
```

Create a new `Command`

```typescript
class NewCommand extends Command {
  
  public constructor(){
    super(CommandName.NEW_COMMAND, [
      ...add required instructions here
    ])
  }
  
}
```

Add command to `CommandMap` in `Commands.ts`

```typescript
const CommandMap: Map<string, Command> = new Map();

CommandMap.set(CommandName.NEW_COMMAND, new NewCommand());
```

# New Pi Setup Procedure

## Setting Up Your New Raspberry Pi
With your new Raspberry Pi, you need to install Raspbian OS onto the SD card for your 



## Installing Dependencies



## Cloning Server Codes

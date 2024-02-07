
export class Colour {

    private red: number;
    private green: number;
    private blue: number;

    constructor(red: number = 0, green: number = 0, blue: number = 0){
        if (this.validateColour(red, green, blue)){
            this.red = red;
            this.green = green;
            this.blue = blue;
        } else {
            console.error("Invalid rgb values")
            this.red = 0;
            this.green = 0;
            this.blue = 0;
        }
    }

    /**
     * Gets the colour based on the devices theme
     * @returns the colour
     */
    public getColour(): { r: number, g: number, b: number } {
        return {
            r: this.red,
            g: this.green,
            b: this.blue
        };
    }

    /**
     * Validates a colour, if the colour provided is not a valid hex code an error will be thrown
     * @param colour the colour to validate
     * @returns true if valid
     */
    private validateColour(red: number, green: number, blue: number): boolean {
        const isValid = (colour: number) => {
            return colour <= 255 && colour >= 0;
        }

        return isValid(red) && isValid(green) && isValid(blue);
    }
}
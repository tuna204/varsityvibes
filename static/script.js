import { irysToExecAddr, execToIrysAddr } from "@irys/js/common/utils";

window.convertAddress = function() {
    const irysAddr = document.getElementById("irys_address_input").value;
    if (!irysAddr) {
        alert("Enter an Irys address first!");
        return;
    }
    const execAddr = irysToExecAddr(irysAddr);
    document.getElementById("exec_address_output").innerText = execAddr;
}

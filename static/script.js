const apiURL = "/api/water_level"

const alarm = document.getElementById("alarm")


function updateWaterLevel(){

fetch(apiURL)

.then(res => res.json())

.then(data => {

let percent = data.water_level || 0

document.getElementById("percent").innerText = percent + "%"

document.getElementById("wave").style.height = percent + "%"


const wave = document.getElementById("wave")


if(percent < 50){

wave.style.background = "#38bdf8"

}

else if(percent < 80){

wave.style.background = "#facc15"

}

else{

wave.style.background = "#ef4444"

}


let status = document.getElementById("status")


if(percent < 80){

status.innerText = "Water Level Normal"

status.style.color = "#4ade80"

alarm.pause()

alarm.currentTime = 0

}

else{

status.innerText = "ALERT: Water Above 80%"

status.style.color = "#f87171"

if(alarm.paused) alarm.play()

}

})

}


function updateAlertsTable(){

fetch("/api/recent_alerts")

.then(res => res.json())

.then(data => {

const table = document.getElementById("alertsTable")

table.innerHTML =
"<tr><th>Water Level</th><th>Timestamp</th></tr>"


data.forEach(alert => {

const row = table.insertRow()

const level = row.insertCell(0)

const time = row.insertCell(1)

level.innerText = alert.level + "%"

time.innerText = alert.time

})

})

}


setInterval(updateWaterLevel,1000)

setInterval(updateAlertsTable,5000)
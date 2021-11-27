

report_template = """
<!DOCTYPE html>
<html>
<title>HMI Automation Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<body>

<div class="w3-container">

<h2 style="text-align:center">HMI Automation Report</h2>
<br>


        <style type="text/css"> 
        .container {
           
            height:200px;
           
            padding-top:10px;
            padding-left:0px;
            padding-right:0px;
        }

        #nd-box {
            float:right;
            width:50%;
            height:200px;            
            border:solid black;
            margin-right:10px;
        }


        </style> 
        
                <style type="text/css"> 
        .collapsible {


  cursor: pointer;

  width: 50%;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;



}

        .collapsible1 {


  cursor: pointer;

  width: 50%;
  border: none;
  text-align: left;
  outline: none;
  font-size: 15px;



}


.active, .collapsible:hover {

}



.collapsible:after {
  content: '-';


  float: right;
  margin-left: 5px;

}

.active:after {
  content: "-";
}


tr:nth-child(4n+0) td,
tr:nth-child(4n+1) td {
    background-color: #EBEDEF;
}

tr:nth-child(4n+2) td,
tr:nth-child(4n+3) td {
    background-color: #EBEDEF;
}


button:nth-child(4n+0),
button:nth-child(4n+1) {
    background-color: #EBEDEF;
}

button:nth-child(4n+2),
button:nth-child(4n+3) {
    background-color: #FFFFFF;
}


.content {
  padding: 0 18px;
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.2s ease-out;
  background-color: #f1f1f1;
}
        .container {
           
            height:200px;
           

            padding-left:0px;
            padding-right:0px;
        }

        #nd-box {
            float:right;
            width:50%;
         


        }
        
        .collapsible:after {
  content: '+'; 
  font-size: 12px;
  color: black;

   font-weight: 900;


}

        .collapsible1:after {
  content: '-'; 
  font-size: 12px;
  color: black;

   font-weight: 900;


}

.active:after {
  content: "+"; /* Unicode character for "minus" sign (-) */
}


        </style> 


      
         
<div class="container" style="border-style:borderless;">      
<div id="piechart" style="border-style:groove;border-width: thin;border-color:#eff5f5;width:40%; float:left;"></div>
<script>
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.maxHeight){
      content.style.maxHeight = null;
    } else {
      content.style.maxHeight = content.scrollHeight + "px";
    } 
  });
}
</script>


<script>
function zzz() {

alert("ff")


}
</script>
<script>
function myFunction(param, rows12) {
var xx = (parseInt(param))
var x = document.getElementById("aaa_"+param);


  

  


 for (i=1;i<=100;i++){ 
 try{
    var y = document.getElementById("bbb_"+param.toString()+"_"+i.toString());
    if (y.style.display==''){
    y.style.display = "none";
    }else{
    y.style.display=''
    }
    
    }catch(err){break;}

    
  }


  if ((xx%2)==0){

x.style.backgroundColor='#FFFF00';
y.style.backgroundColor='#FFFF00';
}else{

x.style.backgroundColor='#FF0000';
y.style.backgroundColor='#FF0000';

}
  
  


}
</script>

<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>

<script type="text/javascript">
// Load google charts
google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);

// Draw the chart and set the chart values
function drawChart() {
  var data = google.visualization.arrayToDataTable([
  ['Result', 'Status'],
  ['NA', {NA}],
  ['FAIL', {FAIL}],
  ['BLOCKED', {BLOCK}],
  ['PASS', {PASS}],

]);

  // Optional; add a title and set the width and height of the chart
  var options = {'title':'Test Statistics', 'width':450, 'height':200};

  // Display the chart inside the <div> element with id="piechart"
  var chart = new google.visualization.PieChart(document.getElementById('piechart'));
  chart.draw(data, options);
}

</script>

<script>
function myFilterFunction() {
  // Declaring variables
  var input, filter, table, tr, td, i;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("myTable");
  tr = table.getElementsByTagName("tr");

  // Looping through all table rows, and hide those who don't match the search query
  for (i = 0; i < tr.length; i++) {
    if (!tr[i].classList.contains('w3-blue')) {
      td = tr[i].getElementsByTagName("td"),
      match = false;
      console.log(td)
      for (j = 0; j < td.length; j++) {
        if (td[j].classList.contains('w3-red')||td[j].classList.contains('w3-green')) {
            if (td[j].innerHTML.toUpperCase().indexOf(filter) > -1) {
              match = true;
              break;
            }
        }
      }
      if (!match) {
        tr[i].style.display = "none";
      } else {
        tr[i].style.display = "";
      }
    }
  }
}
</script>          
            
            
                
          
              
            <div id="nd-box" style="border-style:groove;border-width: thin;border-color:#eff5f5">
            <div style="font-size:12px;padding-left:10px;padding-top:10px;"><b>Test Suit Name : </b>{suite_name}</div>
            <div style="font-size:12px;padding-left:10px;padding-top:10px;"><b>Device Type &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: </b>{device_type}</div>
            <div style="font-size:12px;padding-left:10px;padding-top:10px;"><b>Build &emsp;&emsp;&emsp;&emsp;&emsp;&ensp;: </b>{build}</div>
            <div style="font-size:12px;padding-left:10px;padding-top:10px;"><b>Test Duration &ensp;&nbsp;: </b>{execution_time}</div>
            <div style="font-size:12px;padding-left:10px;padding-top:10px;"><b>Total Tests &emsp;&emsp;&nbsp;: </b>{total_cases}</div>
            <div style="font-size:12px;padding-left:10px;padding-top:10px;"><b>Language &emsp;&emsp;&emsp;: </b>{language}</div>

            </div>
               
              

        </div>
        
        <br>






<input type="text" id="myInput" onkeyup="myFilterFunction()" placeholder="Filter by Status.." title="Type in a Status">
<div class="w3-responsive">
<br>
<table id="myTable" class="w3-table-all w3-small">
<caption style="text-align:left"><h6><b>Test Execution Result</b></h6></caption>
<tr class="w3-blue">
  <th>SI No</th>
  <th>Test ID</th>
  <th>Suite Name</th>
  <th>Test Name</th>
  <th>Summary/Steps</th>
  

  <th>Actual Result</th>
  <th>Status</th>
  <th>Screenshots</th>
</tr>
{test_case}


</table>
</div>



</div>

</body>
</html> 



"""



test_case_row = """

<tr id="bbb_{si_no_id}" style="display:{disp};">
  <td><a href="javascript:myFunction({si_no}, '3')" style="color:blue;">{si_no}</a></td>
  <td>{test_id}</td>
  <td>{sheet_data}</td>
  <td>{test_case_name}</td>
  <td>{summary1}</td>

  <td>{exp_result}</td>

  <td style="color:{font_color}; text-align:center" class="{result_color}">{result}</td>
  <td>
  <a href={srn_path} style="color:blue;">{screenshot}</a>
  </td>
</tr>
"""
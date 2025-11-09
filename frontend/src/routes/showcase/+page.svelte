<script>
  import CuttingBoard from './CuttingBoard.svelte'
  import Start from './Start.svelte'

  let cuttingBoard
</script>

<div id=background>
<Start />
<CuttingBoard bind:this={cuttingBoard} />

<br>

<button id=submit onclick={()=>{cuttingBoard.startAnimation()}}>
  SEGMENT!
</button>

</div>
<style>
  @import "./style.css";
  #background {
    background: 
      repeating-conic-gradient(#89cff0 0 25%, #FFFF 0 50%) 
        50% / 150px 150px;
    position: fixed;
    width: 100%;
    height: 100%;
  }

  #submit {
    z-index: 10;
    position: fixed;
  }
</style>

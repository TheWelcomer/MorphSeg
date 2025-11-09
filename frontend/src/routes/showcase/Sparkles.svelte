<script>
    var numbkle = new Array(20);
    let sparc = "/assets/Sprite-Sparkle.gif";
</script>

<style>
    #sparklid {
        background-color: transparent;
        height: 100%;
        width: 100%;
        float: left;
        position: fixed;
    }
    .sparkle {
        image-rendering: pixelated;
        position: absolute;
        width: 10vmax;
        height: 10vmax;
    }
    #cooked {
        font-size: 10em;
    }
</style>

<div id="sparklid">
    {#each numbkle as _, numb}
        <img class="sparkle" src={sparc} alt="sparkle!" style="left: {Math.random()*110-5}%; top: {Math.random()*110-5}%;">
    {/each}
    <div id="cooked">ALL COOKED!</div>
</div>
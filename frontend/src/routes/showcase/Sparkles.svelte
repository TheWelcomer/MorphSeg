<script>
    var numbkle = [[15,15], [10,25], [23,17], [85,85], [90,70], [63,87], [15,85], [10,70], [23,87], [85,15], [75,13], [25,80]];
</script>

<style>
    #sparklid {
        background-color: transparent;
        height: 75vh;
        width: 80%;
        left: 5%;
        position: absolute;
    }
    .sparkle {
        image-rendering: pixelated;
        position: absolute;
        width: 7vmax;
        height: 7vmax;
        animation: 1s linear 1 both normal zoomin;
        animation-delay: 1.5s;
    }
    @keyframes swirl {
        from {
            transform: rotate(0%);
        }
        to {
            transform: rotate(359%);
        }
    }
    @keyframes zoomin {
        from {
            transform: scale(0.001);
        }
        to {
            transform: scale(1);
        }
    }
</style>

<div id="sparklid">
    {#each numbkle as numbs}
        <img class="sparkle" src="/assets/Sprite-Sparkle Hut!.gif" alt="sparkle!" style="left: {numbs[0]}%; top: {numbs[1]}%;">
    {/each}
</div>
